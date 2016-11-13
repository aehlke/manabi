import React from 'react'
import ReactDOM from 'react-dom'
import Editor from 'draft-js-plugins-editor';
import { EditorState, convertToRaw } from 'draft-js'
// import {convertFromRaw, convertToRaw} from 'draft-js';

import createSingleLinePlugin from 'draft-js-single-line-plugin'
const singleLinePlugin = createSingleLinePlugin({
    stripEntities: false,
})

import createFuriganaPlugin from './draft-js-furigana-plugin/furiganaPlugin'
const furiganaPlugin = createFuriganaPlugin()

const plugins = [
    singleLinePlugin,
    furiganaPlugin,
]

class AnnotatedJapaneseInput extends React.Component {
    constructor(props) {
        super(props)

        this.state = {editorState: EditorState.createEmpty()}

        this.onChange = (editorState) => {
            this.setState({editorState})
        }

        this.logState = () => {
            const content = this.state.editorState.getCurrentContent();
            console.log(convertToRaw(content));
        }
    }

    render() {
        const {editorState} = this.state;
        return <div>
            <Editor
                editorState={editorState}
                onChange={this.onChange}
                plugins={plugins}
                onClick={this.logState}
            />
        </div>
    }
}


ReactDOM.render(
    <AnnotatedJapaneseInput />,
    document.getElementById('annotated-japanese-input')
);
