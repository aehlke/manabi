import decorateComponentWithProps from 'decorate-component-with-props';
import { Map } from 'immutable';
import TextWithFurigana from './Furigana';
import 'whatwg-fetch'
import debounce from 'lodash/debounce'
import furiganaStrategy from './furiganaStrategy';
import { Entity, Modifier, SelectionState } from 'draft-js'

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
        let currentContent = store.getEditorState().getCurrentContent()
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

            let currentContent = store.getEditorState().getCurrentContent()
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

    const updateFurigana = debounce((editorState) => {
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
                applyFurigana(plainText, textWithFuriganaRaw, furiganaPositions)
            })
    }, 250, {maxWait: 1000})

    // Styles are overwritten instead of merged as merging causes a lot of confusion.
    //
    // Why? Because when merging a developer needs to know all of the underlying
    // styles which needs a deep dive into the code. Merging also makes it prone to
    // errors when upgrading as basically every styling change would become a major
    // breaking change. 1px of an increased padding can break a whole layout.
    const {
        theme = defaultTheme,
    } = config;
    const mentionSearchProps = {
        callbacks,
        theme,
        store,
        entityMutability: config.entityMutability ? config.entityMutability : 'SEGMENTED',
        // positionSuggestions,
        // mentionTrigger,
    };
    return {
        decorators: [
            {
                strategy: furiganaStrategy(),
                component: decorateComponentWithProps(TextWithFurigana, { theme }),
            },
        ],

        initialize: ({ getEditorState, setEditorState }) => {
            store.getEditorState = getEditorState;
            store.setEditorState = setEditorState;
        },

        onChange: (editorState) => {
            if (callbacks.onChange) return callbacks.onChange(editorState);

            updateFurigana(editorState)

            return editorState;
        },
    };
};

export default createFuriganaPlugin;
