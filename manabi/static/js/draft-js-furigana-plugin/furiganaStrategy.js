import { Entity } from 'draft-js';

const findFurigana = (trigger) => (character) => {
    const entityKey = character.getEntity();
    return (entityKey !== null && Entity.get(entityKey).getType() === 'FURIGANA');
};

const findFuriganaEntities = (trigger) => (contentBlock, callback) => {
    contentBlock.findEntityRanges(findFurigana(trigger), callback);
};

export default findFuriganaEntities;
