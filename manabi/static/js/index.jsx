import React from 'react'
import ReactDOM from 'react-dom'
import Editor from 'draft-js-plugins-editor';
import { EditorState } from 'draft-js'
import {convertFromRaw, convertToRaw} from 'draft-js';
import 'whatwg-fetch'
import Cookies from 'js-cookie'

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

        this.onChange = (editorState) => {
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
                    console.log(textWithFuriganaRaw)
                })

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
