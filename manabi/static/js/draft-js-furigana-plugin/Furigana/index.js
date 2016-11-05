import React from 'react';
import { Entity } from 'draft-js';
import { fromJS } from 'immutable';
import unionClassNames from 'union-class-names';

#  const MentionLink = ({ mention, children, className }) =>
#    <a
#      href={mention.get('link')}
#      className={className}
#      spellCheck={false}
#    >
#      {children}
#    </a>;
#
#  const MentionText = ({ children, className }) =>
#    <span
#      className={className}
#      spellCheck={false}
#    >
#      {children}
#    </span>;
#


const TextWithFurigana = (props) => {
    const {
        entityKey,
        theme = {},
        children,
        decoratedText,
        className,
    } = props;

    const combinedClassName = unionClassNames(theme.mention, className);
    const furigana = fromJS(Entity.get(entityKey).getData().furigana);

    return (
        <ruby
        entityKey={entityKey}
        theme={theme}
        className={combinedClassName}
        decoratedText={decoratedText}
        >
        {children}
        <rt>{furigana}</rt>
        </ruby>
    );
};

export default TextWithFurigana;
