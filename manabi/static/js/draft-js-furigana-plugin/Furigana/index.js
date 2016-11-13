import React from 'react';
import { Entity } from 'draft-js';
import { fromJS } from 'immutable';

const TextWithFurigana = (props) => {
    const furigana = fromJS(Entity.get(props.entityKey).getData().furigana);
    const entityKey = props.entityKey

    return (
        <ruby>
        {props.children}
        <rt><button type="button" className="btn btn-outline-primary btn-sm">{furigana}</button></rt>
        </ruby>
    );

        // <rt contentEditable={false}><button contentEditable={false} type="button" className="btn btn-outline-primary btn-sm">{furigana}</button></rt>
        //<rt><button type="button" className="btn btn-outline-primary btn-sm">{furigana}</button></rt>

        //<rt contentEditable={false}><button contentEditable={false} type="button" className="btn btn-outline-primary btn-sm">{furigana}</button></rt>
};

export default TextWithFurigana;
