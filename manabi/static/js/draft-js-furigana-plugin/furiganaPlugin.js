import decorateComponentWithProps from 'decorate-component-with-props';
import { Map } from 'immutable';
import TextWithFurigana from './Furigana';
//import MentionSuggestions from './MentionSuggestions';
//import MentionSuggestionsPortal from './MentionSuggestionsPortal';
// import defaultRegExp from './defaultRegExp';
//import mentionStrategy from './mentionStrategy';
//import mentionSuggestionsStrategy from './mentionSuggestionsStrategy';
//import mentionStyles from './mentionStyles.css';
//import mentionSuggestionsStyles from './mentionSuggestionsStyles.css';
// import mentionSuggestionsEntryStyles from './mentionSuggestionsEntryStyles.css';
// import suggestionsFilter from './utils/defaultSuggestionsFilter';
// import defaultPositionSuggestions from './utils/positionSuggestions';

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
        getPortalClientRect: (offsetKey) => clientRectFunctions.get(offsetKey)(),
        getAllSearches: () => searches,
        /*isEscaped: (offsetKey) => escapedSearch === offsetKey,
    escapeSearch: (offsetKey) => {
      escapedSearch = offsetKey;
    },

    resetEscapedSearch: () => {
      escapedSearch = undefined;
    },*/

        /*register: (offsetKey) => {
      searches = searches.set(offsetKey, offsetKey);
    },*/

        /*updatePortalClientRect: (offsetKey, func) => {
      clientRectFunctions = clientRectFunctions.set(offsetKey, func);
    },

    unregister: (offsetKey) => {
      searches = searches.delete(offsetKey);
      clientRectFunctions = clientRectFunctions.delete(offsetKey);
    },*/
    };

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
        //MentionSuggestions: decorateComponentWithProps(MentionSuggestions, mentionSearchProps),
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

        /*onDownArrow: (keyboardEvent) => callbacks.onDownArrow && callbacks.onDownArrow(keyboardEvent),
    onTab: (keyboardEvent) => callbacks.onTab && callbacks.onTab(keyboardEvent),
    onUpArrow: (keyboardEvent) => callbacks.onUpArrow && callbacks.onUpArrow(keyboardEvent),
    onEscape: (keyboardEvent) => callbacks.onEscape && callbacks.onEscape(keyboardEvent),
    handleReturn: (keyboardEvent) => callbacks.handleReturn && callbacks.handleReturn(keyboardEvent),*/
        onChange: (editorState) => {
            if (callbacks.onChange) return callbacks.onChange(editorState);

            this.updateFurigana(editorState)

            return editorState;
        },
    };
};

export default createFuriganaPlugin;
