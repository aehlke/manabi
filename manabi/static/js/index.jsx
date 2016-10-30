import React from 'react'
import ReactDOM from 'react-dom'
import Editor from 'draft-js-plugins-editor';
import { EditorState } from 'draft-js'

import createSingleLinePlugin from 'draft-js-single-line-plugin'
const singleLinePlugin = createSingleLinePlugin()

const plugins = [
    singleLinePlugin,
]


class AnnotatedJapaneseInput extends React.Component {
    constructor(props) {
        super(props)

        this.state = {editorState: EditorState.createEmpty()}
        this.onChange = (editorState) => this.setState({editorState})
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
