import React from 'react'
import ReactDOM from 'react-dom'
import { Editor, Raw, Plain } from 'slate'
import AutoReplace from 'slate-auto-replace'
import Cookies from 'js-cookie'
import debounce from 'lodash/debounce'
import 'whatwg-fetch'

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
                    <rt contentEditable={false}><button contentEditable={false} type="button" className="btn btn-outline-primary btn-sm" spellCheck={false}>ruby</button></rt>
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
    .map(block => block.text)
    .join('\n')
}


class AnnotatedJapaneseInput extends React.Component {
    constructor(props) {
        super(props)

        this.state = {
            state: initialState,
        }

        this.lastFetchedFuriganaText = null

        // this.updateFurigana = debounce(this._updateFurigana, 250, {maxWait: 1000})

        // Fail-safe.
        setInterval(() => {
            this.updateFurigana()
        }, 3000);
    }

    applyFurigana = (plainText, textWithFuriganaRaw, furiganaPositions) => {
        console.log("apply")

        let { state } = this.state

        // console.log(Raw.serialize(state))
        // console.log(state.transform()inlines)

        // TODO: Save current selection to restore at end.
        // TODO: Compare raw prefix with textWithFuriganaRaw to decide whether to reject.

        // Move selection to start.
        let firstTextNode = state.document.getTexts().first()
        let startRange = state.selection.merge({
            anchorKey: firstTextNode.key,
            anchorOffset: 0,
            focusKey: firstTextNode.key,
            focusOffset: 0,
        })
        state = state
            .transform()
            .moveTo(startRange)
            .apply()

        var currentOffset = 0

        // Does not land within textWithFurigana nodes, but counts their surface length
        // when passing through them. If it would land within one, it instead lands
        // immediately after it.
        function moveForward(state, n) {
            console.log("moveForward: will move forward", n)
            for (var i = 0; i < n; i++) {
                let currentInline = state.inlines.get(0)
                let landingInsideFurigana = (
                    currentInline && currentInline.type === 'textWithFurigana')

                console.log("modeForward: moving forward by 1")
                state = state
                    .transform()
                    .moveForward(1)
                    .apply()

                if (landingInsideFurigana) {
                    let surface = serializeNodesToText(currentInline.get('nodes'))
                    console.log("moveForward: Landing inside furigana...", surface)
                    i += surface.length
                    currentOffset += surface.length

                    if (i > n) {
                        // We're ending midway into existing furigana.
                        return {
                            state: state,
                            landedInsideFurigana: true,
                        }
                    }
                } else {
                    currentOffset += 1
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
            console.log("furiganaStart", furiganaStart, "furiganaEnd", furiganaEnd)
            // Try to move forward to start of intended furigana.
            let moveForwardResult = moveForward(state, furiganaStart - currentOffset)
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

            let surface = serializeNodesToText(state.fragment.nodes)
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
                .collapseToEnd()
                .apply()
            this.onChange(state)
            currentOffset += furiganaEnd - furiganaStart
        }

        /*while (currentOffset < 20) {
            // 52:    return state.inlines.some(inline => inline.type == 'link')
            // if state.inlines
            let currentInline = state.inlines.get(0)
            if (currentInline && currentInline.type === 'textWithFurigana') {
                console.log("found furigana inline", currentInline)
                let data = currentInline.get('data')
                let furigana = data.get('furigana')
                // let surface = data.get('surface')
                let surface = currentInline.children
                console.log(furigana, surface)

                currentOffset += surface.length
                console.log("moved forward ", surface.length, "(found furigana)...")
            }

            state = state
                .transform()
                .moveForward(1)
                .apply()
            currentOffset += 1
            console.log("moved forward 1...")
        }*/

        /*state = state
            .transform()
            .insertInline({
                type: 'textWithFurigana',
                isVoid: true,
                data: {
                    furigana: 'foo-furigana',
                    surface: 'foo-surface',
                },
            })
            .extendBackward(2)
            .wrapInline({
                type: 'textWithFurigana',
                isVoid: true,
                data: { },
            })
            .collapseToEnd()
            .apply()*/

        this.onChange(state)
    }

    updateFurigana = debounce(() => {
        let plainText = Plain.serialize(this.state.state)
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
                onChange={this.onChange}
            />
        )
    }
}


ReactDOM.render(
    <AnnotatedJapaneseInput />,
    document.getElementById('annotated-japanese-input')
);
