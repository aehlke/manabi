import React from 'react'
import ReactDOM from 'react-dom'
import { Editor, Raw, Plain } from 'slate'
import AutoReplace from 'slate-auto-replace'
import Cookies from 'js-cookie'
import debounce from 'lodash/debounce'
import 'whatwg-fetch'
import Immutable from 'immutable'

const csrfToken = Cookies.get('csrftoken')


const initialState = Plain.deserialize('')

const schema = {
    nodes: {
        textWithFurigana: (props) => {
            const { state, node } = props
            const { data } = node
            // const code = data.get('code')
            const furigana = data.get('furigana')
            const surface = data.get('surface')
            const isSelected = state.selection.hasFocusIn(node)

            return (
                <ruby className={`${isSelected ? 'selected' : ''}`}>
                    {surface}
                    <rt contentEditable={false}><button contentEditable={false} type="button" className="btn btn-outline-primary btn-sm" spellCheck={false}>{furigana}</button></rt>
                </ruby>
            )

            return (
                <span >
                    {props.children}
                <ruby contentEditable={false} className={`${isSelected ? 'selected' : ''}`}>
                    <rt contentEditable={false}><button contentEditable={false} type="button" className="btn btn-outline-primary btn-sm" spellCheck={false}>ruby</button></rt>
                </ruby>
                </span>
            )
        },
    }
}


function serializeNodesToText(nodes) {
    return nodes
        .map(node => {
            if (node.type === 'textWithFurigana') {
                return node.get('data').get('surface')
            } else if (typeof node.nodes === 'undefined') {
                return node.text
            }
            return node.nodes
                .map(node => {
                    if (node.kind === 'text') {
                        return node.text
                    } else if (node.type === 'textWithFurigana') {
                        return node.get('data').get('surface')
                    } else {
                        throw new Error("Unexpected node type found in serializer.")
                    }
                })
                .join('')
        })
        .join('\n')
}


function moveToNextNode(state, parentNode, currentNode) {
    let nextNode = parentNode.getNextSibling(currentNode.key)
    console.log(nextNode)
    let nextRange = state.selection.merge({
        anchorKey: nextNode.key,
        anchorOffset: 0,
        focusKey: nextNode.key,
        focusOffset: 0,
    })
    return state
        .transform()
        .moveTo(nextRange)
        .apply()
}


class AnnotatedJapaneseInput extends React.Component {
    constructor(props) {
        super(props)

        this.state = {
            state: initialState,
        }

        this.tmp = {}
        this.tmp.compositions = 0
        this.tmp.isComposing = false
        this.lastFetchedFuriganaText = null

        // this.updateFurigana = debounce(this._updateFurigana, 250, {maxWait: 1000})

        // Fail-safe.
        setInterval(() => {
            this.updateFurigana()
        }, 2300);
    }

    applyFurigana = (plainText, textWithFuriganaRaw, furiganaPositions) => {
        console.log("apply")

        let { state } = this.state

        // console.log(Raw.serialize(state))
        // console.log(state.transform()inlines)

        // TODO: Save current selection to restore at end.
        // TODO: Compare raw prefix with textWithFuriganaRaw to decide whether to reject.


        var currentOffset = 0

        // Does not land within textWithFurigana nodes, but counts their surface length
        // when passing through them. If it would land within one, it instead lands
        // immediately after it.
        //
        // Assumes nothing is selected (as we only use this for moving the cursor).
        // Also assumes the document is a *single block* (as we only use single line inputs).
        function moveForward(state, n) {
            console.log("moveForward: will move forward", n)
            console.log(Raw.serialize(state))
            let parentNode = state.document.nodes.first()
            for (var i = 0; i < n; i++) {
                console.log("moveForward: top of loop.", i, n, currentOffset)
                // Are we at the end of a text node?
                if (state.texts.first()) {
                    let textNode = state.texts.first()
                    if (state.selection.anchorOffset === textNode.length) {
                        // At end of a text node; move to next node.
                        console.log("At end of a text node; move to next node.")
                        state = moveToNextNode(state, parentNode, textNode)
                    }
                }
                // console.log("inlines?", state.inlines)
                // console.log("text?", state.texts.first())
                let currentInline = state.inlines.get(0)
                let landingInsideFurigana = (
                    currentInline && currentInline.type === 'textWithFurigana')

                if (landingInsideFurigana) {
                    let surface = serializeNodesToText(Immutable.List.of(currentInline))
                    console.log("moveForward: Landing inside furigana...", currentInline, surface)
                    i += (surface.length - 1)
                    currentOffset += surface.length

                    console.log("Inside furigana node; moving to next node.")
                    console.log("set i to", i, "currentOFfset at", currentOffset)
                    state = moveToNextNode(state, parentNode, currentInline)
                    console.log(state.selection)

                    if (i > n) {
                        // We're ending midway into existing furigana.
                        console.log("moveForward: Ending midway into existing furigana...")
                        return {
                            state: state,
                            landedInsideFurigana: true,
                        }
                    }
                } else {
                    console.log("modeForward: moving forward by 1")
                    state = state
                        .transform()
                        .moveForward(1)
                        .apply()
                    currentOffset += 1
                }

                // If at end of a text node, move to the start of the next node.
                let textNode = state.texts.first()
                if (textNode && state.selection.anchorOffset === textNode.length) {
                    state = moveToNextNode(state, parentNode, textNode)
                    console.log("At end of text node; moved to start of next.")
                }
            }
            console.log("moveForward: moved forward, currentOffset is", currentOffset)
            return {
                state: state,
                landedInsideFurigana: false,
            }
        }

        // Assumes these are already sorted ascending.
        for (let [furiganaStart, furiganaEnd, furigana] of furiganaPositions) {
            // Move selection to start.
            let firstNode = state.document.nodes.first()//getTexts().first()
            let startRange = state.selection.merge({
                anchorKey: firstNode.key,
                anchorOffset: 0,
                focusKey: firstNode.key,
                focusOffset: 0,
            })
            state = state
                .transform()
                .moveTo(startRange)
                .apply()
            currentOffset = 0

            console.log("furiganaStart", furiganaStart, "furiganaEnd", furiganaEnd)
            // Try to move forward to start of intended furigana.
            let moveForwardResult = moveForward(state, furiganaStart) // - currentOffset)
            state = moveForwardResult.state

            if (moveForwardResult.landedInsideFurigana) {
                console.log("Landed inside furigana; moving on to next candidate.")
                continue
            }

            // Select the desired furigana range.
            console.log("Select desired range of length", furiganaEnd-furiganaStart)
            state = state
                .transform()
                .extendForward(furiganaEnd - furiganaStart)
                .apply()

            // Were we able to select the intended number of characters, or did we hit the end?
            if (
                state.selection.focusOffset - state.selection.anchorOffset
                !== furiganaEnd - furiganaStart
            ) {
                console.log("Couldn't select enough characters for furigana range.")
                break
            }

            // Does a furigana already cover the desired range?
            console.log("Does a furigana already cover the desired range?")
            console.log('selected offsets', state.selection.anchorOffset, state.selection.focusOffset)
            // console.log(state.texts.first() ? serializeNodesToText(state.fragment.nodes) : '..not text..')
            console.log(state.inlines.first())
            console.log(state.inlines.first() ? state.inlines.first().kind : '')
            if (state.inlines.some(inline => inline.type === 'textWithFurigana')) {
                // Skip this furigana; already covered.
                console.log("Skipping as this range contains furigana already.")
                state = state
                    .transform()
                    .collapseToStart()
                    .apply()
                continue
            }

            // Apply the furigana.
            console.log("Going to apply the furigana...", furigana)
            console.log(Raw.serialize(state))
            console.log(state.selection.anchorKey)
            console.log(state.selection.focusOffset)
            console.log(state.selection.anchorOffset)
            var surface
            if (state.inlines.length > 0) {
                surface = serializeNodesToText(state.fragment.nodes)
            } else {
                surface = state.startText.text.substring(
                    state.selection.anchorOffset, state.selection.focusOffset)
            }
            console.log("Applying furigana to range!", surface, furigana)
            state = state
                .transform()
                .wrapInline({
                    type: 'textWithFurigana',
                    isVoid: true,
                    data: {
                        furigana: furigana,
                        surface: surface,
                    },
                })
                .apply()
            this.onChange(state)
            currentOffset += furiganaEnd - furiganaStart
        }

        console.log("finished furigana application.")
        console.log("")
        this.onChange(state)
    }

    updateFurigana = debounce(() => {
        // IME is active?
        if (this.tmp.isComposing) {
            return
        }

        let plainText = serializeNodesToText(this.state.state.document.nodes)
        console.log("updateFurigana", plainText)

        if (plainText.trim() === '') {
            return
        }

        if (this.lastFetchedFuriganaText === plainText) {
            return
        }

        this.lastFetchedFuriganaText = plainText

        let url = 'http://dev.manabi.io:8000/api/furigana/inject/'
        fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({text: plainText}),
        })
            .then((response) => response.json())
            .then((json) => {
                let textWithFuriganaRaw = json['text_with_furigana']
                let furiganaPositions = json['furigana_positions']

                this.applyFurigana(plainText, textWithFuriganaRaw, furiganaPositions)
            })
    }, 250, {maxWait: 1000})

    onCompositionStart = (e) => {
        this.tmp.isComposing = true
        this.tmp.compositions++
    }
    onCompositionEnd = (e) => {
        const count = this.tmp.compositions

        // The `count` check here ensures that if another composition starts
        // before the timeout has closed out this one, we will abort unsetting the
        // `isComposing` flag, since a composition in still in affect.
        setTimeout(() => {
            if (this.tmp.compositions > count) return
            this.tmp.isComposing = false
        })
    }

    onChange = (state) => {
        console.log('onChange')
        this.setState({ state })
    }

    // On change, update the app's React state with the new editor state.
    render() {
        return (
            <Editor
                state={this.state.state}
                plugins={this.plugins}
                schema={schema}
                onCompositionEnd={this.onCompositionEnd}
                onCompositionStart={this.onCompositionStart}
                onChange={this.onChange}
            />
        )
    }
}


ReactDOM.render(
    <AnnotatedJapaneseInput />,
    document.getElementById('annotated-japanese-input')
);
