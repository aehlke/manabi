import Debug from 'debug'
import React from 'react'
import ReactDOM from 'react-dom'
import { Editor, Raw, Plain, Document, State, Block, Text, Inline } from 'slate'
import AutoReplace from 'slate-auto-replace'
import Cookies from 'js-cookie'
import debounce from 'lodash/debounce'
import 'whatwg-fetch'
import Immutable from 'immutable'

const debug = function(){} //console.log //Debug('manabi')

const csrfToken = Cookies.get('csrftoken')

// TODO: Load in initial state from backend or from query param.
// TODO: Hook up serialized form to form submission.
// TODO: Spinner / loading activity indicator.

class TextWithFurigana extends React.Component {

    render() {
        return (
            <ruby contentEditable={false} className={`${this.props.isSelected ? 'selected' : ''}`}>
                {this.props.surface}
                <rt contentEditable={false}>
                    <button
                        contentEditable={false}
                        type="button"
                        className="btn btn-outline-primary btn-sm"
                        spellCheck={false}
                        onClick={this.props.furiganaButtonOnClick}
                    >{this.props.furigana}</button>
                </rt>
            </ruby>
        )
    }
}

function deserializeCharacter(char) {
  return { text: char }
}

const manabiRawRegex = /([^《》｜]*)｜([^《》｜]*)《([^《》｜]*)》([^《》｜]*)/g
function deserializeFromManabiRawFormat(value) {
    var match = null, nodes = []

    function addTextNode(text) {
        nodes.push(Text.create({ characters: text.split('').map(deserializeCharacter) }))
    }

    if (manabiRawRegex.exec(value) === null) {
        addTextNode(value)
    }
    manabiRawRegex.lastIndex = 0  // Reset.

    while ((match = manabiRawRegex.exec(value)) !== null) {
        let prefix = match[1]
        let surface = match[2]
        let furigana = match[3]
        let suffix = match[4]

        addTextNode(prefix)

        if (furigana.length > 0) {
            nodes.push(Inline.create({
                type: 'textWithFurigana',
                isVoid: true,
                data: {
                    furigana: furigana,
                    surface: surface,
                },
            }))
        } else if (surface.length > 0) {
            addTextNode(surface)
        }

        addTextNode(suffix)
    }

    return State.create({
        document: Document.create({
            nodes: [Block.create({
                type: 'line',
                nodes: nodes,
            })],
        }),
    })
}

// Does not iterate into nested nodes.
function nodeText(node, textWithFuriganaFormatter = null) {
    if (node.type === 'textWithFurigana') {
        if (textWithFuriganaFormatter) {
            return textWithFuriganaFormatter(node)
        }
        return node.get('data').get('surface')
    } else if (node.kind === 'text') {
        return node.text
    } else {
        throw new Error("Unexpected node type found in serializer.")
    }
}

function serializeNodesToText(nodes, textWithFuriganaFormatter = null) {
    return nodes
        .map(node => {
            if (typeof node.nodes === 'undefined') {
                return nodeText(node, textWithFuriganaFormatter)
            }
            return node.nodes
                .map(node => nodeText(node, textWithFuriganaFormatter))
                .join('')
        })
        .join('\n')
}

function serializeToManabiRawFormat(state) {
    return serializeNodesToText(state.document.nodes, function (node) {
        let data = node.get('data')
        return `｜${data.get('surface')}《${data.get('furigana')}》`
    })
}

// Returns the offset from the start of the document, in count of characters.
// Assumes a single block (for single-line inputs).
function cursorOffset(state) {
    let { selection } = state
    // let nodes = state.document.nodes.toJS()[0].nodes
    let nodes = state.document.nodes.first().get('nodes')

    if (selection.anchorKey !== selection.focusKey) {
        throw new Error("cursorOffset only works on 0-length selections.")
    }

    var accumulatedText = ''

    for (let node of nodes) {
        let text = nodeText(node)
        let targetNodeFound = selection.anchorKey === node.key
        if (targetNodeFound) {
            text = text.substring(0, selection.anchorOffset)
        }
        accumulatedText += text
        if (targetNodeFound) {
            break
        }
    }
    return accumulatedText.length
}

function moveToNextNode(state, parentNode, currentNode) {
    debug('moveToNextNode(...)')
    debug("Current node is", currentNode)
    var nextNode = parentNode.getNextSibling(currentNode.key)
    if (nextNode.type === 'textWithFurigana') {
        // Must always select a text node.
        nextNode = nextNode.nodes.first()
    }
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

function moveSelectionToEnd(state) {
    let lastTextNode = state.document.nodes.first().nodes.last()
    let startRange = state.selection.merge({
        anchorKey: lastTextNode.key,
        anchorOffset: lastTextNode.length - 1,
        focusKey: lastTextNode.key,
        focusOffset: lastTextNode.length - 1,
    })
    return state
        .transform()
        .moveTo(startRange)
        .apply()
}

class AnnotatedJapaneseInput extends React.Component {
    constructor(props) {
        super(props)

        this.hasInitializedFurigana = false

        let initialState = (
            deserializeFromManabiRawFormat(window.annotatedJapaneseInputInitialValue || ""))

        initialState = moveSelectionToEnd(initialState)

        this.state = { state: initialState }

        this.tmp = {}
        this.tmp.compositions = 0
        this.tmp.isComposing = false
        this.lastFetchedFuriganaText = null
        this.lastFetchedFuriganaPositions = null
        this.lastAppliedFuriganaText = null
        this.lastAppliedFuriganaPositions = null

        // Fail-safe.
        setInterval(() => {
            this.updateFurigana()
        }, 500);

        this.updateFurigana()
    }

    manabiRawFormatValue = () => {
        return serializeToManabiRawFormat(this.state.state)
    }

    plainText = () => {
        return serializeNodesToText(this.state.state.document.nodes)
    }

    maybeIMEActive = () => {
        return this.tmp.isComposing
    }

    applyFurigana = (plainText, furiganaPositions) => {
        debug("applyFurigana(...)")

        if (
            this.lastAppliedFuriganaText === plainText
            && this.lastAppliedFuriganaPositions === furiganaPositions
        ) {
            return
        }

        if (this.maybeIMEActive()) {
            return
        }

        let { state } = this.state

        // Only apply furigana when nothing is actively selected.
        if (state.selection.anchorKey !== state.selection.focusKey
            || state.selection.anchorOffset !== state.selection.focusOffset
        ) {
            return
        }
        let cursorOffsetBeforeApplication = cursorOffset(state)

        if (plainText
            !== (serializeNodesToText(state.document.nodes).substring(0, plainText.length))
        ) {
            debug("Content diverged since fetching furigana; throwing out.")
            return
        }

        var currentOffset = 0

        function moveToStart(state) {
            debug("moveToStart(...)")
            let firstTextNode = state.document.nodes.first().nodes.first()
            debug("moveToStart: first node selected:", firstTextNode.toJS())
            debug("moveToStart: document", state.document.nodes.first().toJS())
            let startRange = state.selection.merge({
                anchorKey: firstTextNode.key,
                anchorOffset: 0,
                focusKey: firstTextNode.key,
                focusOffset: 0,
            })
            currentOffset = 0
            return state
                .transform()
                .moveTo(startRange)
                .apply()
        }

        function moveForwardToFirstNonEmptyNode(state) {
            debug('moveForwardToFirstNonEmptyNode()')
            let parentNode = state.document.nodes.first()
            let textNode = state.texts.first()
            if (state.selection.isAtEndOf(textNode)) {
                debug("moveForwardToFirstNonEmptyNode: moving forward")
                try {
                    state = moveToNextNode(state, parentNode, textNode)
                } catch (e) {
                    // TODO: Catch a specific error type here, for when no next node.
                }
            }
            return state
        }

        // Does not land within textWithFurigana nodes, but counts their surface length
        // when passing through them. If it would land within one, it instead lands
        // immediately after it.
        //
        // Assumes nothing is selected (as we only use this for moving the cursor).
        // Also assumes the document is a *single block* (as we only use single line inputs).
        function moveForward(state, n) {
            debug("moveForward: will move forward", n)
            debug(Raw.serialize(state))
            let parentNode = state.document.nodes.first()
            for (var i = 0; i < n; i++) {
                debug("moveForward: top of loop.", i, n, currentOffset)
                // Are we at the end of a text node?
                if (parentNode.type !== 'textWithFurigana' && state.texts.first()) {
                    let textNode = state.texts.first()
                    if (state.selection.isAtEndOf(textNode)) {
                        // At end of a text node; move to next node.
                        debug("At end of a text node; move to next node.", textNode)
                        try {
                            state = moveToNextNode(state, parentNode, textNode)
                        } catch (e) {
                            // TODO: Catch a specific error type here, for when no next node.
                        }
                    }
                }

                let currentInline = state.inlines.get(0)
                let landingInsideFurigana = (
                    currentInline && currentInline.type === 'textWithFurigana')

                if (landingInsideFurigana) {
                    let surface = currentInline.data.get('surface')
                    debug("moveForward: Landing inside furigana...", currentInline, surface)
                    i += (surface.length - 1)
                    debug("currentOffset was at", currentOffset)
                    currentOffset += surface.length

                    debug("Inside furigana node;", surface ,"moving to next node.")
                    debug("set i to", i, "currentOFfset at", currentOffset)
                    try {
                        state = moveToNextNode(state, parentNode, currentInline)
                    } catch (e) {
                        // TODO: Catch a specific error type here, for when no next node.
                    }
                    debug(state.selection)

                    if (i > n) {
                        // We're ending midway into existing furigana.
                        debug("moveForward: Ending midway into existing furigana...")
                        return {
                            state: state,
                            landedInsideFurigana: true,
                        }
                    }
                } else {
                    debug("modeForward: moving forward by 1 (incl currentOffset which was at", currentOffset, ")")
                    state = state
                        .transform()
                        .moveForward(1)
                        .apply()
                    currentOffset += 1
                }

                // If at end of a text node, move to the start of the next node.
                let textNode = state.texts.first()
                if (textNode && state.selection.anchorOffset === textNode.length) {
                    try {
                        state = moveToNextNode(state, parentNode, textNode)
                    } catch (e) {
                        // TODO: Catch a specific error type here, for when no next node.
                    }
                    debug("At end of text node; moved to start of next.")
                }
            }
            debug("moveForward: moved forward, currentOffset is", currentOffset)
            return {
                state: state,
                landedInsideFurigana: false,
            }
        }

        // Assumes these are already sorted ascending.
        for (let [furiganaStart, furiganaEnd, furigana] of furiganaPositions) {
            debug("furiganaStart", furiganaStart, "furiganaEnd", furiganaEnd)
            state = moveToStart(state)
            debug("moved to start... currentOffset at", currentOffset)
            debug(state.document.nodes.first().toJS())

            // Try to move forward to start of intended furigana.
            let moveForwardResult = moveForward(state, furiganaStart) // - currentOffset)
            state = moveForwardResult.state

            if (moveForwardResult.landedInsideFurigana) {
                debug("Landed inside furigana; moving on to next candidate.")
                continue
            }

            // Make sure we're not in an empty in-between text node.
            state = moveForwardToFirstNonEmptyNode(state)

            // Select the desired furigana range.
            debug("Select desired range of length", furiganaEnd-furiganaStart)
            state = state
                .transform()
                .extendForward(furiganaEnd - furiganaStart)
                .apply()

            // Were we able to select the intended number of characters, or did we hit the end?
            if (
                state.selection.focusOffset - state.selection.anchorOffset
                !== furiganaEnd - furiganaStart
            ) {
                debug("Couldn't select enough characters for furigana range.")
                break
            }

            // Does a furigana already cover the desired range?
            debug("Does a furigana already cover the desired range?")
            debug('selected offsets', state.selection.anchorOffset, state.selection.focusOffset)
            if (state.inlines.some(inline => inline.type === 'textWithFurigana')) {
                // Skip this furigana; already covered.
                debug("Skipping as this range contains furigana already.")
                state = state
                    .transform()
                    .collapseToStart()
                    .apply()
                continue
            }

            // Apply the furigana.
            debug("Going to apply the furigana...", furigana)
            var surface
            if (state.inlines.length > 0) {
                surface = serializeNodesToText(state.fragment.nodes)
            } else {
                surface = state.startText.text.substring(
                    state.selection.anchorOffset, state.selection.focusOffset)
            }
            debug("Applying furigana to range!", surface, furigana)
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

        debug("finished furigana application.")
        debug("")

        debug("Restoring cursor position to", cursorOffsetBeforeApplication)
        state = moveToStart(state)
        state = moveForward(state, cursorOffsetBeforeApplication).state

        this.lastAppliedFuriganaText = plainText
        this.lastAppliedFuriganaPositions = furiganaPositions

        this.onChange(state)
    }

    updateFurigana = debounce(() => {
        if (this.maybeIMEActive()) {
            return
        }

        // Not sure why this is needed, yet.
        if (!this.state.state.document) {
            return
        }

        let plainText = serializeNodesToText(this.state.state.document.nodes)
        if (plainText.trim() === '') {
            this.lastFetchedFuriganaText = null
            this.lastFetchedFuriganaPositions = null
            return
        }

        if (this.lastFetchedFuriganaText === plainText) {
            this.applyFurigana(plainText, this.lastFetchedFuriganaPositions)
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
                let furiganaPositions = json['furigana_positions']
                this.lastFetchedFuriganaPositions = furiganaPositions

                this.applyFurigana(plainText, furiganaPositions)

                this.hasInitializedFurigana = true
            })
    }, 250, {maxWait: 1000})

    promptToUpdateFurigana = (node) => {
        let { data } = node
        let surface = data.get('surface')
        let furigana = data.get('furigana')

        let newFurigana = window.prompt(
            `Enter the intended furigana reading for 「${surface}」.`,
            furigana)

        if (newFurigana !== null) {
            let { state } = this.state

            data.furigana = newFurigana
            let properties = {
                data: {
                    furigana: newFurigana,
                    surface: surface,
                },
            }

            state = state
                .transform()
                .setNodeByKey(node.key, properties)
                .apply()
            this.setState({ state })
        }
    }

    schema = {
        nodes: {
            textWithFurigana: (props) => {
                const { state, node } = props
                const { data } = node

                function furiganaButtonOnClick(e) {
                    e.preventDefault()

                    // TODO: Race condition; once the debug package releases with
                    // fix for mis-detecting Electron, use it with debug=slate:transform
                    // to diagnose what is triggering the onChange reversion immediately
                    // after our data update and get rid of this ugly hack.
                    setTimeout(function() {
                        this.promptToUpdateFurigana(props.node)
                    }.bind(this), 10)
                }

                const surface = data.get('surface')
                const furigana = data.get('furigana')

                return (
                    <TextWithFurigana
                        furigana={data.get('furigana')}
                        surface={data.get('surface')}
                        isSelected={this.hasInitializedFurigana && state.selection.hasFocusIn(node)}
                        furiganaButtonOnClick={furiganaButtonOnClick.bind(this)}
                    />
                )
            },
        },
    }

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

    collapseToSingleLine = (state) => {
        let lineNodes = state.document.nodes
        let firstLineNode = lineNodes.first()
        if (lineNodes.size > 1) {
            var transformingState = state.transform()
            for (let lineNode of lineNodes.slice(1)) {
                var nodeCounter = 0
                let innerNodes = lineNode.nodes
                // Skip first node if it's an empty text.
                if (innerNodes.first().length === 0) {
                    innerNodes = innerNodes.shift()
                }
                for (let node of innerNodes) {
                    transformingState = transformingState
                        .moveNodeByKey(
                            node.key,
                            firstLineNode.key,
                            firstLineNode.length + nodeCounter,
                        )
                    nodeCounter += 1
                }

                transformingState = transformingState
                    .removeNodeByKey(lineNode.key)
            }
            state = transformingState.apply()
            return state
        }

        // TODO: strip newlines?
        // See https://github.com/icelab/draft-js-single-line-plugin/blob/7abdf477c6d619dae841c57d79cffe74dba11780/lib/index.js#L70 for example.
        return state
    }

    onChange = (state) => {
        debug('onChange')

        state = this.collapseToSingleLine(state)
        debug(state.document.nodes.toJS())
        debug(Raw.serialize(state))

        this.setState({ state })
    }

    // On change, update the app's React state with the new editor state.
    render() {
        return (
            <span>
                <Editor
                    placeholder={'Japanese Expression'}
                    placeholderStyle={{color: '#999'}}
                    state={this.state.state}
                    plugins={this.plugins}
                    schema={this.schema}
                    onCompositionEnd={this.onCompositionEnd}
                    onCompositionStart={this.onCompositionStart}
                    onChange={this.onChange}
                />
                <input
                    type={'hidden'}
                    name={'expression'}
                    value={this.plainText()}
                    readOnly={true}
                />
                <input
                    type={'hidden'}
                    name={'reading'}
                    value={this.manabiRawFormatValue()}
                    readOnly={true}
                />
            </span>
        )
    }
}


ReactDOM.render(
    <AnnotatedJapaneseInput />,
    document.getElementById('annotated-japanese-input')
);
