
/********************
 ********************
 *
 * Disclaimer to those reading this code!
 *
 *
 * I wrote this module as I was really still learning Javascript and Dojo (and
 * Django), several years ago. I didn't get how to properly 
 * organize OO JS via prototypes, and so on. So please forgive the mess 
 * that this is :) I think my later output is much cleaner. It will be 
 * rewritten eventually, though it works somehow.
 * It's beyond the point of reasonable incremental refactoring.
 * I'll try to fix this stuff up soon though before it bites me back.
 *********************/




//TODO-OLD all this code and globals really need to be encapsulated
//this is a start on encapsulating new stuff I add:
//object to hold things for the Fact Add dialog.
var fact_add_ui = {};

fact_add_ui.keyboardShortcutConnection = null;

fact_add_ui.setKeyboardShortcuts = function() {
    if (fact_add_ui.keyboardShortcutConnection === null) {
        fact_add_ui.keyboardShortcutConnection = dojo.connect(factAddDialog, 'onKeyPress', function(e) {
            var k = dojo.keys;

            // isCopyKey doesn't work here since cmd isn't seen as a modifier key
            if (e.ctrlKey) {
                switch(e.charOrCode) {
                    case k.ENTER:
                        //submit form
                        dojo.stopEvent(e);
                        fact_add_ui.factAddFormSubmit();
                        break;
                }
            }
        });
    }
};

fact_add_ui.unsetKeyboardShortcuts = function() {
    dojo.disconnect(fact_add_ui.keyboardShortcutConnection);
    fact_add_ui.keyboardShortcutConnection = null;
};


function ajaxLink(url, container_id) {
    dijit.byId(container_id).set('href', url);
}



function factFormSubmit(submitSuccessCallback, submitErrorCallback, _factAddForm, factId, showStandby) {
    if (showStandby) {
        factAddFormSubmitButton.set('disabled', true);
    }
    var factAddFormValue = _factAddForm.get('value');
    
    var tempCardCounter = 0;
    for (var key in factAddFormValue) {
        if (key.indexOf('card_template') === 0 && factAddFormValue[key].length) {
            tempCardCounter++;
        }
    }

    //get count of field contents
    var field_content_count = dojo.query('.field_content', _factAddForm.domNode).length;

    factAddFormValue['fact-fact_type'] = 1; //FIXME temp hack - assume Japanese
    factAddFormValue['field_content-TOTAL_FORMS'] = field_content_count.toString(); //fieldContentInputCount.toString();
    factAddFormValue['field_content-INITIAL_FORMS'] = factId ? field_content_count.toString() : '0'; //fieldContentInputCount; 
    
    var xhrArgs = {
        url: factId ? '/flashcards/internal-api/facts/' + factId + '/' : '/flashcards/internal-api/facts/',
        content: factAddFormValue,
        handleAs: 'json',
        load: dojo.hitch(null, function(tempCardCounter, data){
            if (data.success) {
                submitSuccessCallback(data, tempCardCounter);
                //if the fact editing grid is open, update it
                if (typeof cards_factsGrid != 'undefined') {
                    var store = cards_factsGrid.store;
                    store.close();
                    store.fetch();
                    cards_factsGrid.sort();
                }
            } else {
                submitErrorCallback(data, tempCardCounter);
            }
        }, tempCardCounter),
        error: function(error){
            submitErrorCallback(data, tempCardCounter); //TODO-OLD other callback
        }
    };
    dojo.xhrPost(xhrArgs);
}

function resetFactAddForm() {
    //factAddForm.reset(); //don't reset everything... just the field contents
    dojo.query('.dijitTextBox:not([type=hidden]), .dijitTextarea:not([type=hidden])',factAddForm.domNode).forEach(function(node, index, arr){
        var field = dijit.getEnclosingWidget(node);
        field.set('value', '');
        // force an onChange event, to be safe
        field.onChange();
    });

    //reset multi-choice fields
    dojo.query('.dijitSelect', dojo.byId('factFields')).forEach(function(node, index, arr) {
        var widget = dijit.getEnclosingWidget(node);
        widget.set('value', 'none');
    });

    //reset hidden fields
    dojo.query('.hiddenFieldLink', factAddForm.domNode).forEach(function(node) {
        node.style.display = '';
        dojo.query(node).next()[0].style.display = 'none';
    });

    //reset example sentence fields
    var subfact_container = dojo.byId('cardSubfactFormsContainer');
    dojo.query('#cardSubfactFormsContainer').empty().style('display', 'none');
    //subfact_container.attr('content', '');
    //subfact_container.domNode.style.display = 'none';

    //reset the tags input
    //dojo.query('#cardTagsInput')
    $('#cardTagsList').tagit('removeAll');

    //destroy any error messages
    dojo.query('.field_content_error', dojo.byId('factAddFormWrapper')).empty();

    //focus the first text field
    //dojo.query('.dijitTextBox:not([type=hidden]):first-of-type, .dijitTextarea:not([type=hidden]):first-of-type', factAddDialog.domNode).query('input')[0].focus(); //FIXME for textboxes
    dojo.query('.dijitTextBox:not([type=hidden]) input, .dijitTextArea:not([type=hidden])', factAddForm.domNode)[0].focus(); //FIXME for textboxes
}

function createFieldInputsForUpdate(domNode, factTypeId, factFieldValues, cardTemplatesOnCompleteCallback, factFieldsOnCompleteCallback) { //todo:refactor into 2 meths
    if (factTypeId) {
        //add card template options
        var cardUpdateTemplatesStore = new dojo.data.ItemFileReadStore({url: '/flashcards/internal-api/facts/'+factFieldValues['fact-id'][0]+'/card_templates/'});
        var cardUpdateTemplatesButton = new DropDownMultiSelect({inputId: 'cardUpdateTemplatesInput'+factTypeId});//TODO-OLD counter suffix
        var cardUpdateTemplatesInput = dijit.byId('cardUpdateTemplatesInput'+factTypeId);
        
        //hidden form elements, for fact id
        //var hiddenFactField = new dijit.form.TextBox({value:'PUT', name:'_method', type:'hidden'});//dojo.place('<input type=\"hidden\" name=\"fact\" value=\"'+factTypeId+'\">', domNode, 'last');
        //hiddenFactField.placeAt(domNode, 'last');
        hiddenFactField = new dijit.form.TextBox({value:factTypeId, name:'fact-id', type:'hidden'});//dojo.place('<input type=\"hidden\" name=\"fact\" value=\"'+factTypeId+'\">', domNode, 'last');
        hiddenFactField.placeAt(domNode, 'last');
        cardUpdateTemplatesButton.placeAt(domNode, 'last');
            //todo:pull values from the fact store for that id
        var formPrefix = 'form_'+factTypeId+'-';
        var cardTemplateCounter = 0;
        cardUpdateTemplatesStore.fetch({
            onItem: function(item){
                if (cardUpdateTemplatesStore.getValue(item, 'activated_for_fact')) {
                    cardUpdateTemplatesInput.addOption({value: cardUpdateTemplatesStore.getValue(item, 'card_template').id+"", label: cardUpdateTemplatesStore.getValue(item, 'card_template').name, selected: 'selected'});
                } else {
                    cardUpdateTemplatesInput.addOption({value: cardUpdateTemplatesStore.getValue(item, 'card_template').id+"", label: cardUpdateTemplatesStore.getValue(item, 'card_template').name});
                }
            },
            onComplete: function(items) {
                cardTemplatesOnCompleteCallback(items);
            }
        });
        
        //add FieldContent textboxes (based on Fields)
        var fieldsStore = new dojo.data.ItemFileReadStore({url:'/flashcards/internal-api/fact_types/'+factTypeId+'/fields/', clearOnClose:true}); //todo:try with marked up one instead
        var fieldCounter = 0;
        fieldsStore.fetch({
            onItem: function(item) {
                var tempFieldCounter = fieldCounter++; 
                var fieldContentHeaderHTML = '<div><strong>'+fieldsStore.getValue(item, 'name')+':</strong>';
                if (!fieldsStore.getValue(item, 'blank')) {
                    fieldContentHeaderHTML += ' (required)';
                }
                dojo.place(fieldContentHeaderHTML, domNode, 'last');
                dojo.place('<div id="id_field_content-'+tempFieldCounter+'-content-errors" class="field_content_error" />', domNode, 'last');
                var fieldTextarea = new dijit.form.SimpleTextarea({
                    name: 'field_content-'+tempFieldCounter+'-content', //fieldsStore.getValue(item, 'name'),
                    'class': 'field_content',
                    id: formPrefix+'id_field_content-'+tempFieldCounter+'-content',
                    jsId: formPrefix+'id_field_content_'+tempFieldCounter+'_content',
                    value: factFieldValues['id'+fieldsStore.getValue(item, 'id')][0],//"",
                    style: "width:300px;",
                    rows: '2'
                }).placeAt(domNode, 'last');
                fieldTextarea.set('gridStoreItemId', 'id'+fieldsStore.getValue(item, 'id')); //TODO-OLD this is a hack - all this code needs to be refactored
                
                new dijit.form.TextBox({
                    name: 'field_content-'+tempFieldCounter+'-field_type',
                    id: formPrefix+'id_field_content-'+tempFieldCounter+'-field_type',
                    jsId: formPrefix+'id_field_content_'+tempFieldCounter+'_field_type',
                    value: fieldsStore.getValue(item, 'id'),
                    type: 'hidden'
                }).placeAt(domNode, 'last');
                
                new dijit.form.TextBox({
                    name: 'field_content-'+tempFieldCounter+'-id',
                    value: factFieldValues['id'+fieldsStore.getValue(item, 'id')+'_field-content-id'][0],
                    type: 'hidden'
                }).placeAt(domNode, 'last');

                dojo.place('</div>', domNode, 'last');
            },
            onComplete: function(items) {
                fieldContentInputCount = fieldCounter;
                factFieldsOnCompleteCallback(items);
            }
        });
    }
}


var factTypeInputOnChangeHandle = null;
var lastCardTemplatesInputValue = null;
var fieldContentInputCount = 4;//FIXME this is a terrible legacy hack... 

function appendLineToAddedCardHistory(node, text) {
    //append a line, but if there are too many lines, delete the first line
    existing_lines = node.innerHTML.split('<br>');
    if (existing_lines.length > 4) {
        //delete first line
        existing_lines.shift();
        node.innerHTML = existing_lines.join('<br>');
    } else if (existing_lines.length == 1) {
        text = '<br>' + text;
    }
    node.innerHTML += text + '<br>';
}

fact_add_ui.factAddFormSubmit = function() {
    //var cardTemplatesInput = dijit.byId('cardTemplatesInput');
    factFormSubmit(function(data, tempCardCounter){
        // Success callback
        //dojo.place('Added '+tempCardCounter.toString()+' cards for '+factAddFormValue['field_content-0-content']+'<br>','factAddFormResults', 'last');
        if (dojo.trim(factAddFormResults.containerNode.innerHTML) === '') {
            factAddFormResults.containerNode.innerHTML = '';
        }
        appendLineToAddedCardHistory(factAddFormResults.containerNode, 'Added '+tempCardCounter.toString()+' cards for '+dijit.byId('id_field_content-0-content').get('value'));
        resetFactAddForm();
        factAddFormSubmitButton.set('disabled', false);
    }, function(data, tempCardCounter) {
        // Error callback
        //show field_content errors
        fieldContentErrors = data.error.field_content;//[errors][field_content];
        factAddFormSubmitButton.set('disabled', false);

        dojo.forEach(fieldContentErrors, function(errorMsg, idx) {
            if ('content' in errorMsg) {
                dojo.byId('id_field_content-'+idx+'-content-errors').innerHTML = '<font color="red"><em>'+errorMsg.content.join('<br>')+'</em></font>';
            } else {
                var node_to_empty = dojo.byId('id_field_content-'+idx+'-content-errors');
                if (node_to_empty) {
                    dojo.empty(node_to_empty);
                }
            }
        });
        
        if (data.error.fact.length && 'tags' in data.error.fact[0]) {
            dojo.byId('fact-tag-errors').innerHTML = '<font color="red"><em>' + data.error.fact[0].tags.join('<br>') + '</em></font>';
        } else {
            dojo.query('#fact-tag-errors').empty();
        }

        factAddFormSubmitButton.set('disabled', false);
    }, factAddForm, null, true);
};



//------------------------------------------

//the new class for fact editing
fact_ui = {};

dojo.addOnLoad(function() {
    fact_ui.facts_grid_normal_height = '300px'; //TODO-OLD figure out how to make the height as tall as window
    fact_ui.facts_grid_minimized_height = '145px';
});


fact_ui.showFactEditForm = function(fact_id, submit_success_callback) {
    //fact_ui.selected_fact_row_index = row_index;
    fact_ui._submit_success_callback = submit_success_callback;

    //cards_factsGrid.domNode.style.height = fact_ui.facts_grid_minimized_height;
    //cards_factsGrid.resize();
    //cards_factsGrid.scrollToRow(row_index); //TODO-OLD this can be a little awkward, moving too often
    cards_factEditorContainer.set('href', 'flashcards/facts/' + fact_id + '/update/');
    //cards_factEditorContainer.domNode.style.display = '';
    cards_factEditorContainer.show();
    dojo.query('.dijitDialogCloseIcon',cards_factEditorContainer.domNode)[0].style.visibility='hidden';
};

fact_ui.hideFactEditForm = function() {
    //cards_factEditorContainer.domNode.style.display = 'none';
    //cards_factEditorContainer.attr('content', '');
    //re-expand the facts grid
    //cards_factsGrid.domNode.style.height = fact_ui.facts_grid_normal_height;
    //cards_factsGrid.resize();
    cards_factEditorContainer.hide();
};

fact_ui.submitFactForm = function(fact_form, fact_id) {
    // currently used for updating facts
    //factForm must be a dijit form
    //fact_id is optional - if specified, it means we're updating a fact
    //TODO-OLD return a deferred instead of taking in success/error callbacks

    //disable the submit button while processing
    submit_button = dijit.getEnclosingWidget(dojo.query('input[type=submit]', fact_form.domNode)[0]);
    submit_button.set('disabled', true);

    form_values = fact_form.get('value');

    var card_counter = 0;
    dojo.query('.card_templates input', fact_form.domNode).forEach(function(cardInput) {
        cardInput = dijit.getEnclosingWidget(cardInput);
        var val = cardInput.get('value');
        if (val !== false) {
            var new_key = 'card-' + (card_counter++) + '-template';
            form_values[new_key] = val;
        }
    });
    
    /*var card_templates_input = dijit.getEnclosingWidget(dojo.query('.card_templates', fact_form.domNode)[0]);
    /var card_templates = card_templates_input.get('value');
    var card_counter = 0;
    dojo.forEach(card_templates, function(val) {
        var new_key = 'card-' + (card_counter++) + '-template';
        form_values[new_key] = val;
    });*/
    
    //get the number of fields
    field_count = dojo.query('.cards_fieldContent', fact_form.domNode).length;

    //assemble the form submission values
    //form_values['fact-fact_type'] = '1'; //TODO-OLD temp hack - assume Japanese
    form_values['card-TOTAL_FORMS'] = card_counter.toString();
    form_values['card-INITIAL_FORMS'] = '0';
    form_values['field_content-TOTAL_FORMS'] = field_count.toString();
    /*form_values['field_content-INITIAL_FORMS'] = 
        fact_id ? field_count.toString() : '0';*/

    //submit the form
    var submit_error_callback = function(data, card_counter) {
        field_content_errors = data.error.field_content;
        dojo.forEach(field_content_errors, function(error_message, idx) {
            //idx corresponds to the nth field content
            field_content_error_divs = dojo.query('.field_content_error', fact_form.domNode);
            if ('content' in error_message) {
                field_content_error_divs[idx].innerHTML = error_message.content.join('<br>');
            } else {
                dojo.empty(field_content_error_divs[idx]);
            }
        });
    };

    var xhrArgs = {
        url: fact_id ? 
                    '/flashcards/internal-api/facts/' + fact_id + '/' : 
                    '/flashcards/internal-api/facts/',
        content: form_values,
        handleAs: 'json',
        load: function(data){
            if (data.success) {
                fact_ui._submit_success_callback(data, card_counter);

            } else {
                submit_error_callback(data, card_counter);
            }
            submit_button.set('disabled', false);
        },
        error: function(error){
            submit_error_callback(data, card_counter); //TODO-OLD other callback for this
            submit_button.set('disabled', false);
        }
    };
    dojo.xhrPost(xhrArgs); //var deferred = 
    //dojo.place('Added '+tempCardCounter.toString()+' cards for '+'what'+'<br>','factAddFormResults', 'last');
};

fact_ui.facts_url_query = {fact_type: 1};

fact_ui.clearFilter = function(filter_name) {
    var store = cards_factsGrid.store;
    store.close();
    delete fact_ui.facts_url_query[filter_name];
    store.url = '/flashcards/internal-api/facts/?' + dojo.objectToQuery(fact_ui.facts_url_query);
    store.fetch();
    cards_factsGrid.sort(); //forces a refresh
};


fact_ui.clearFactSearch = function() {
    var cards_factSearchField = dijit.byId('cards_factSearchField');
    fact_ui.current_search_url_parameter = '';
    cards_factSearchField.set('value', '');
    cards_clearFactSearchButton.domNode.style.visibility = 'hidden';
    fact_ui.clearFilter('search');
};

fact_ui.clearTagFilters = function() {
    var cards_factFilterByTagInput = dijit.byId('cards_factFilterByTagInput');
    fact_ui.current_tag_filter_list = [];
    cards_factFilterByTagInput.reset();
    cards_clearTagFiltersButton.domNode.style.visibility = 'hidden';
    fact_ui.clearFilter('tags');
};

//fact_ui.addTagFilterDiv = function(container_node) {
//    container_node.

fact_ui._generateReading = function(expression) {
    //outputs the reading for expression to the reading_field
    //var expression = expression_field.attr('value');
    var ret_def = new dojo.Deferred();
    var xhr_args = {
        url: '/flashcards/internal-api/generate_reading/',
        content: {expression: expression},
        handleAs: 'json',
        headers: { "Content-Type": "application/x-www-form-urlencoded; charset=utf-8" },
        load: dojo.hitch(null, function(success_def, data) {
            if (data.success) {
                success_def.callback(data.data);
            } else {
                success_def.errback(data); //FIXME errback?
            }
        }, ret_def)
    };
    dojo.xhrPost(xhr_args);
    return ret_def;
};

fact_ui.generateReading = function(expression, reading_field, show_standby) {
    reading_field = dijit.byId(reading_field);
    //TODO-OLD why is this duplicated in the arguments?
    if (expression.trim() !== '') {
        reading_field.set('disabled', true);        

        var def = fact_ui._generateReading(expression);

        var standby = null;

        if (show_standby) {
            standby = new dojox.widget.Standby({
                target: dijit.byId(reading_field).domNode.id
            });
            dojo.body().appendChild(standby.domNode);
            standby.startup();
            standby.show();
        }
        def.addCallback(dojo.hitch(null, function(reading_field, expression, standby, reading) {
            if (reading.trim()) { // != expression.trim()) {
                reading_field.set('value', reading);
            }
            if (standby) {
                standby.hide();
                standby.destroy();
            }
            dijit.byId(reading_field).set('disabled', false);            
        }, dijit.byId(reading_field), expression, standby));
    } else {
        dijit.byId(reading_field).set('value', '');
    }
};


fact_ui.showFactAddDialog = function(deckId) {
    if (typeof deckId == 'undefined') { deckId = null; }
    factAddDialog.show();

    if (deckId) {
        deckInput.attr('value', deckId.toString());
    }
};


fact_ui._addSubfactForm = function(target_node, field_content_offset, subfact_form_template, subfact_form_field_count) {
    index_array = Array();
    for (var i=field_content_offset; i<subfact_form_field_count+field_content_offset; i++) {
        index_array.push(i);
    }
    //console.log(index_array);
    var subfact_form_string = dojo.string.substitute(subfact_form_template, index_array);
    //target_node = dijit.byId(target_node);

    //console.log(target_pane);
    target_node.style.display = '';
    //console.log(target_pane.containerNode);
    var new_pane = new dojox.layout.ContentPane({content: subfact_form_string});
    new_pane.placeAt(target_node, 'last');
    new_pane.startup();
    dojo.query('input,textarea', new_pane.containerNode).first()[0].scrollIntoView();
    // scroll to the bottom of the parent pane
    //var anim = dojox.fx.smoothScroll({
    //    node: dojo.query('input,textarea', new_pane.containerNode).first(),
    //    win: target_pane,
    //    duration:300,
    //    easing:dojo.fx.easing.easeOut
    //}).play();
    //console.log(anim);
    
    //dojo.place(dojo.create('div', {innerHTML:subfact_form_string}), target_pane.containerNode, 'last'); //attr('content', target_pane.attr('content') + subfact_form_string);
    //target_pane.attr('content', target_pane.attr('content') + subfact_form_string);
};

fact_ui.addSubfactFormLink = function(target_node, fact_form_node, subfact_form_template, subfact_form_field_count) {
    // onclick function for link that adds a subfact form (like for example
    // sentences)

    // count field contents already in the form
    var field_content_offset = dojo.query('[name^=field_content-][name$=-content]', fact_form_node).length;
    //console.log(field_content_offset);
    
    fact_ui._addSubfactForm(target_node, field_content_offset, subfact_form_template, subfact_form_field_count);
};

fact_ui.removeSubfactForm = function(subfact_node, subfact_pane) {
    // Removes a subfact form from a fact editor form.
    // If it's for a bound form (for a subfact which already exists), it
    // hides that form and sets that fact to DELETE.

    // get the contentpane which contains the subfact node
    var cp = null;
    var container_node = dojo.query(subfact_node).parent();
    var parent_container = container_node.closest('.subfact_container_pane')[0];
    var delete_field = dojo.query(subfact_node).query('[name^=fact-][name$=-DELETE]:first');

    if (delete_field.length) {
        delete_field.set('value', 'on');
        container_node[0].style.display = 'none';
        // move the cp out of its parent
        container_node.place(parent_container, 'before');
    } else {
        if (cp) {
            cp.destroyRecursive();
        } else {
            dojo.destroy(container_node[0]);//subfact_node[0]);
        }
    }
    if (!dojo.query(parent_container).children().length) { //!dojo.query(parent_container).attr('content').trim()) {
        parent_container.style.display = 'none';
    }
};


