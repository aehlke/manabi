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
            const isSelected = state.selection.hasFocusIn(node)

                /*return(
                <span contentEditable={false} className="textWithFurigana" {...props.attributes}>🍔</span>
            )*/

            return (
                <ruby contentEditable={false} className={`${isSelected ? 'selected' : ''}`}>
                    foo {props.children} bar
                    <rt contentEditable={false}><button contentEditable={false} type="button" className="btn btn-outline-primary btn-sm">ruby</button></rt>
                </ruby>
            )
        },
    }
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

        state = state
            .transform()
            .insertInline({
                type: 'textWithFurigana',
                isVoid: true,
                data: { },
            })
            /*.extendBackward(2)
            .wrapInline({
                type: 'textWithFurigana',
                isVoid: true,
                data: { },
            })
            .collapseToEnd()*/
            .apply()

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
