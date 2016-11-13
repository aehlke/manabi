import React from 'react';
import { Entity } from 'draft-js';
import { fromJS } from 'immutable';

const TextWithFurigana = (props) => {
    const furigana = fromJS(Entity.get(props.entityKey).getData().furigana);
    const entityKey = props.entityKey

    return (
        <ruby>
        {props.children}
        <rt><button>{furigana}</button></rt>
        </ruby>
    );
};

export default TextWithFurigana;
