import React from 'react'
import ReactDOM from 'react-dom'
import Editor from 'draft-js-plugins-editor';
import { EditorState, Entity, Modifier, SelectionState } from 'draft-js'
import {convertFromRaw, convertToRaw} from 'draft-js';
import 'whatwg-fetch'
import Cookies from 'js-cookie'
import debounce from 'lodash/debounce'

import createSingleLinePlugin from 'draft-js-single-line-plugin'
const singleLinePlugin = createSingleLinePlugin()

import createFuriganaPlugin from './draft-js-furigana-plugin/furiganaPlugin'
const furiganaPlugin = createFuriganaPlugin()

const plugins = [
    singleLinePlugin,
    furiganaPlugin,
]

const csrfToken = Cookies.get('csrftoken')

class AnnotatedJapaneseInput extends React.Component {
    constructor(props) {
        super(props)

        this.state = {editorState: EditorState.createEmpty()}

        this.applyFurigana = (plainText, textWithFuriganaRaw, furiganaPositions) => {
            let currentContent = this.state.editorState.getCurrentContent()
            let blockMap = currentContent.getBlockMap()

            // We assume only plain text + kanji entitites.
            var offset = 0
            var invalidated = false
            blockMap.forEach((block) => {
                // If the input has diverged since the API call, invalidate the results.
                let blockPlainText = block.getText()
                if (invalidated || blockPlainText != plainText.substr(offset, blockPlainText.length)) {
                    console.log('diverged, throwing out API response...')
                    console.log(blockPlainText); console.log(plainText)
                    invalidated = true
                    return
                }

                let currentContent = this.state.editorState.getCurrentContent()
                let endOffset = offset + block.getText().length
                // console.log(block.getText())

                for (let [furiganaStart, furiganaEnd, furigana] of furiganaPositions) {
                    if (furiganaStart > endOffset || furiganaEnd > endOffset) {
                        break
                    }

                    let furiganaStartInBlock = furiganaStart - offset
                    let furiganaEndInBlock = furiganaEnd - offset

                    // Check that there's no existing furigana within this range.
                    var hasExistingFuriganaInRange = false
                    for (let furiganaInnerIndex = furiganaStartInBlock; furiganaInnerIndex < furiganaEndInBlock; furiganaInnerIndex++ ) {
                        if (block.getEntityAt(furiganaInnerIndex) != null) {
                            hasExistingFuriganaInRange = true
                            break
                        }
                    }
                    if (hasExistingFuriganaInRange) {
                        continue
                    }

                    let furiganaEntityKey = Entity.create('FURIGANA', 'SEGMENTED', {furigana: furigana})
                    let surfaceSelection = new SelectionState({
                        anchorKey: block.getKey(),
                        anchorOffset: furiganaStartInBlock,
                        focusKey: block.getKey(),
                        focusOffset: furiganaEndInBlock,
                    })
                    let furiganaEntity = Modifier.applyEntity(
                        currentContent,
                        surfaceSelection,
                        furiganaEntityKey,
                    )
                }

                offset += block.getText()
            })
        }

        let updateFurigana = debounce((editorState) => {
            let plainText = editorState.getCurrentContent().getPlainText('')

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

        this.onChange = (editorState) => {
            updateFurigana(editorState)

            this.setState({editorState})
        }
    }

    render() {
        const {editorState} = this.state;
        return <Editor
            editorState={editorState}
            onChange={this.onChange}
            plugins={plugins}
        />
    }
}


ReactDOM.render(
    <AnnotatedJapaneseInput />,
    document.getElementById('annotated-japanese-input')
);
