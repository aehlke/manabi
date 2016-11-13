import { Map } from 'immutable';
import TextWithFurigana from './Furigana';
import 'whatwg-fetch'
import debounce from 'lodash/debounce'
import furiganaStrategy from './furiganaStrategy';
import { Entity, Modifier, SelectionState, EditorState, convertToRaw } from 'draft-js'
import Cookies from 'js-cookie'

const csrfToken = Cookies.get('csrftoken')

const createFuriganaPlugin = (config = {}) => {
    const defaultTheme = {
        /*// CSS class for mention text
    mention: mentionStyles.mention,
        // CSS class for suggestions component
    mentionSuggestions: mentionSuggestionsStyles.mentionSuggestions,
        // CSS classes for an entry in the suggestions component
    mentionSuggestionsEntry: mentionSuggestionsEntryStyles.mentionSuggestionsEntry,
    mentionSuggestionsEntryFocused: mentionSuggestionsEntryStyles.mentionSuggestionsEntryFocused,
    mentionSuggestionsEntryText: mentionSuggestionsEntryStyles.mentionSuggestionsEntryText,
    mentionSuggestionsEntryAvatar: mentionSuggestionsEntryStyles.mentionSuggestionsEntryAvatar,*/
    };

    const callbacks = {
        keyBindingFn: undefined,
        handleKeyCommand: undefined,
        onDownArrow: undefined,
        onUpArrow: undefined,
        onTab: undefined,
        onEscape: undefined,
        handleReturn: undefined,
        onChange: undefined,
    };

    let searches = Map();
    let escapedSearch;
    let clientRectFunctions = Map();

    const store = {
        getEditorState: undefined,
        setEditorState: undefined,
    };

    const applyFurigana = (plainText, textWithFuriganaRaw, furiganaPositions) => {
        var editorState = store.getEditorState()
        let blockMap = editorState.getCurrentContent().getBlockMap()
        console.log("furigana positions:", furiganaPositions)

        // We assume only plain text + kanji entitites.
        var offset = 0
        var furiganaAdded = false
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

            let endOffset = offset + block.getText().length

            /*block.findEntityRanges(function(){return true}, function(start,end) {
                console.log("find entity ranges:", start, end)
            })*/

            for (let [furiganaStart, furiganaEnd, furigana] of furiganaPositions) {
                if (furiganaStart > endOffset || furiganaEnd > endOffset) {
                    break
                }

                let currentContent = editorState.getCurrentContent()
                let furiganaStartInBlock = furiganaStart - offset
                let furiganaEndInBlock = furiganaEnd - offset

                // Check that there's no existing furigana within this range.
                var hasExistingFuriganaInRange = false
                console.log("gonna try to find existing furigana...", furiganaStartInBlock, furiganaEndInBlock)
                // TODO Consolidate w/ furiganaStrategy
                block.findEntityRanges(
                    function (character) {
                        const entityKey = character.getEntity();
                        return (entityKey !== null && Entity.get(entityKey).getType() === 'FURIGANA');
                    },
                    function(entityStart, entityEnd) {
                        console.log("should I bail on adding furigana? the existing one", entityStart, entityEnd, "and the furigana position I want to add", furiganaStartInBlock, furiganaEndInBlock)
                        if (furiganaStartInBlock >= entityStart && furiganaEndInBlock <= entityEnd) {
                            console.log("ALREADY HAS FURIGANA!")
                            hasExistingFuriganaInRange = true
                        }
                    },
                )
                console.log("checked.")
                /*for (let furiganaInnerIndex = furiganaStartInBlock; furiganaInnerIndex < furiganaEndInBlock; furiganaInnerIndex++ ) {
                    console.log("checking entity at index:", furiganaInnerIndex, block.getEntityAt(furiganaInnerIndex))
                    if (block.getEntityAt(furiganaInnerIndex) != null) {
                        console.log("ALREADY HAS FURIGANA!")
                        hasExistingFuriganaInRange = true
                        break
                    }
                }*/
                if (hasExistingFuriganaInRange) {
                    continue
                }

                let furiganaEntityKey = Entity.create('FURIGANA', 'IMMUTABLE', {furigana: furigana})
                let surfaceSelection = new SelectionState({
                    anchorKey: block.getKey(),
                    anchorOffset: furiganaStartInBlock,
                    focusKey: block.getKey(),
                    focusOffset: furiganaEndInBlock,
                })

                let textToReplace = block.getText().substring(
                    furiganaStartInBlock, furiganaEndInBlock)

                let furiganaEntityAppliedState = Modifier.replaceText(
                    currentContent,
                    surfaceSelection,
                    textToReplace,
                    null,
                    furiganaEntityKey,
                )

                editorState = EditorState.push(
                    editorState,
                    furiganaEntityAppliedState,
                    'apply-furigana',
                )

                furiganaAdded = true
            }

            offset += block.getText()
        })

        if (furiganaAdded) {
            console.log("furigana added! pushing state...")
            console.log(convertToRaw(editorState.getCurrentContent()));
            store.setEditorState(editorState)
            console.log(convertToRaw(store.getEditorState().getCurrentContent()));
        }
    }

    const updateFurigana = debounce((editorState) => {
        let plainText = editorState.getCurrentContent().getPlainText('')

        if (plainText.trim() === '') {
            return
        }

        if (store.lastFetchedFuriganaText === plainText) {
            return
        }

        store.lastFetchedFuriganaText = plainText

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

                applyFurigana(plainText, textWithFuriganaRaw, furiganaPositions)
            })
    }, 250, {maxWait: 1000})

    const {
    } = config;
    return {
        decorators: [
            {
                strategy: furiganaStrategy,
                component: TextWithFurigana,
            },
        ],

        initialize: ({ getEditorState, setEditorState }) => {
            store.getEditorState = getEditorState
            store.setEditorState = setEditorState

            store.lastFetchedFuriganaText = null

            // Fail-safe.
            setInterval(function() {
               updateFurigana(store.getEditorState())
            }, 1000);
        },

        // handlePastedText: (text, html) => {
        //     console.log('pasted')
        //     updateFurigana(store.getEditorState())
        // },
        //
        // handleBeforeInput: (chars) => {
        //     console.log('before input')
        //     updateFurigana(store.getEditorState())
        // },

        onChange: (editorState) => {
            // console.log("onChange in plugin")
            // if (store.getEditorState().getCurrentContent() !== editorState.getCurrentContent()) {
            //     console.log("changed!")
            // //     // console.log(store.getEditorState().getCurrentContent())
            // //     // updateFurigana(editorState)
            // }
            updateFurigana(editorState)

            return editorState;
        },
    };
};

export default createFuriganaPlugin;
