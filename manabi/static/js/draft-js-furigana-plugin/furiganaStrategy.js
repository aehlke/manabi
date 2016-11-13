import { Entity } from 'draft-js';

const furiganaStrategy = (contentBlock, callback) => {
    contentBlock.findEntityRanges(
        (character) => {
            const entityKey = character.getEntity()
            if (entityKey === null) {
                return false
            }
            return Entity.get(entityKey).getType() === 'FURIGANA'
        },
        callback,
    )
}

export default furiganaStrategy
