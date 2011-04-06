
(function($) {

    $.fn.tagit = function(options) {

        var settings = {
            'itemName'          : 'item',
            'fieldName'         : 'tags',
            'availableTags'     : [],
            // callback: called when a tag is added
            'onTagAdded'        : null,
            // callback: called when a tag is removed
            'onTagRemoved'      : null,
            // callback: called when a tag is clicked
    	    'onTagClicked'      : null,
            'tagSource':
                function(search, showChoices) {
                    var filter = new RegExp(search.term, 'i');
                    var choices = settings.availableTags.filter(function(element) {
                        return (element.search(filter) != -1);
                    });
                    showChoices(subtractArray(choices, assignedTags()));
                },
            'removeConfirmation': false,
            'caseSensitive': true,
            'allowSpaces': false, // when enabled, quotes are not neccesary for inputting multi-word tags

            // The below options are for using a single field instead of several for our form values.
            'singleField': false, // When enabled, will use a single hidden field for the form, rather than one per tag.
                                  // It will delimit tags in the field with singleFieldDelimiter.
            'singleFieldDelimiter': ',',
            'singleFieldNode': null, // Set this to an input DOM node to use an existing form field.
                                    // Any text in it will be erased on init. But it will be populated with 
                                    // the text of tags as they are created, delimited by singleFieldDelimiter.
                                    // If this is not set, we create an input node for it, with the name 
                                    // given in settings.fieldName, ignoring settings.itemName.

            'tabIndex': null // Optionally set a tabindex attribute on the input that gets created for tag-it.
        };

        if (options) {
            $.extend(settings, options);
        }

        var tagList = $(this),
            tagInput  = $('<input class="tagit-input" type="text" ' + (settings.tabIndex ? 'tabindex="' + settings.tabIndex + '"' : '') + '/>');
            BACKSPACE = 8,
            ENTER     = 13,
            SPACE     = 32,
            COMMA     = 44,
            TAB       = 9;

        tagList
            // add the tagit CSS class.
            .addClass('tagit')
            // create the input field.
            .append($('<li class="tagit-new"></li>\n').append(tagInput))
            .click(function(e) {
                if (e.target.className == 'close') {
                    // Removes a tag when the little 'x' is clicked.
                    // Event is binded to the UL, otherwise a new tag (LI > A) wouldn't have this event attached to it.
                    removeTag($(e.target).parent());
                } else if (e.target.className == 'tagit-label' && settings.onTagClicked) {
                    settings.onTagClicked($(e.target).parent());
                } else {
                    // Sets the focus() to the input field, if the user clicks anywhere inside the UL.
                    // This is needed because the input field needs to be of a small size.
                    tagInput.focus();
                }
            })
            // add existing tags
            .children('li')
                .each(function() {
                    if (!$(this).hasClass('tagit-new')) {
                        createTag($(this).html(), $(this).attr('class'));
                        $(this).remove();
                    }
                });

        if (settings.singleField) {
            if (settings.singleFieldNode) {
                // Add existing tags from the input field
                var node = $(settings.singleFieldNode);
                var tags = node.val().split(settings.singleFieldDelimiter);
                node.val('');
                $.each(tags, function(index, tag) {
                    createTag(tag);
                });
            } else {
                // Create our single field input after our list.
                settings.singleFieldNode = tagList.after('<input type="hidden" style="display:none;" value="" name="' + settings.fieldName + '" />');
            }
        }

        tagInput
            .keydown(function(event) {
                var keyCode = event.keyCode || event.which;
                // Backspace is not detected within a keypress, so using a keydown
                if (keyCode == BACKSPACE && tagInput.val() == '') {
                    var tag = tagList.children('.tagit-choice:last');
                    if (!settings.removeConfirmation || tag.hasClass('remove')) {
                        // When backspace is pressed, the last tag is deleted.
                        removeTag(tag);
                    } else if (settings.removeConfirmation) {
                        tag.addClass('remove');
                    }
                }
            })
            .keypress(function(event) {
                var keyCode = event.keyCode || event.which;
                // Comma/Space/Enter are all valid delimiters for new tags. except when there is an open quote or if setting allowSpaces = true
                if (
                    keyCode == COMMA ||
                    keyCode == ENTER ||
                    keyCode == TAB ||
                    (
             	        keyCode == SPACE && 
             	        settings.allowSpaces != true &&
				        (
					        ($.trim(tagInput.val()).replace( /^s*/, '' ).charAt(0) != '"') ||
					        (
					            $.trim(tagInput.val()).charAt(0) == '"' &&
					            $.trim(tagInput.val()).charAt($.trim(tagInput.val()).length - 1) == '"' &&
					            $.trim(tagInput.val()).length - 1 != 0
					        )
				        )
                    )
                ) {

                    event.preventDefault();
                    createTag(cleanedInput());
                }
                if (settings.removeConfirmation) {
                    tagList.children('.tagit-choice:last').removeClass('remove');
                }
            }).blur(function(e){
                // create a tag when the element loses focus (nothing will happen if it's empty though)
                createTag(cleanedInput());
		    });
            

        if (options.availableTags || options.tagSource) {
            tagInput.autocomplete({
                source: settings.tagSource,
                select: function(event, ui) {
                    // Delete the last tag if we autocomplete something despite the input being empty
                    // This happens because the input's blur event causes the tag to be created when
                    // the user clicks an autocomplete item.
                    // The only artifact of this is that while the user holds down the mouse button
                    // on the selected autocomplete item, a tag is shown with the pre-autocompleted text,
                    // and is changed to the autocompleted text upon mouseup.
                    if (tagInput.val() == '') {
                        removeTag(tagList.children('.tagit-choice:last'));
                    }
                    createTag(ui.item.value);
                    // Preventing the tag input to be updated with the chosen value.
                    return false;
                }
            });
        }

        function cleanedInput() {
            // Returns the contents of the tag input, cleaned and ready to be passed to createTag
            return $.trim(tagInput.val().replace(/^'|"$|,+$/g, ''));
        }

        function assignedTags() {
            // Returns an array of tag string values
            var tags = [];
            if (settings.singleField) {
                tags = $(settings.singleFieldNode).val().split(settings.singleFieldDelimiter);
                if (tags[0] == '') {
                    tags = [];
                }
            } else {
                tagList.children('.tagit-choice').each(function() {
                    tags.push(tagLabel(this));//$(this).children('input').val());
                });
            }
            return tags;
        }
        function updateSingleTagsField(tags) {
            // Takes a list of tag string values, updates settings.singleFieldNode.val to the tags delimited by settings.singleFieldDelimiter
            $(settings.singleFieldNode).val(tags.join(settings.singleFieldDelimiter));
        }
        function subtractArray(a1, a2) {
            var result = new Array();
            for (var i = 0; i < a1.length; i++) {
                if (a2.indexOf(a1[i]) == -1) {
                    result.push(a1[i]);
                }
            }
            return result;
        }
        function tagLabel(tag) {
            // Returns the tag's string label.
            if (settings.singleField) {
                return $(tag).children('.tagit-label').text();
            } else {
                return $(tag).children('input').val();
            }
        }
        function isNew(value) {
            var isNew = true;
            tagList.children('.tagit-choice').each(function(i) {
                if (formatStr(value) == formatStr(tagLabel(this))) {
                    isNew = false;
                    return;
                }
            });
            return isNew;
        }
	    function formatStr(str) {
		    if(settings.caseSensitive) {
			    return str;
            }
		    return $.trim(str.toLowerCase());
	    }
        function createTag(value, additionalClass) {
            // Automatically trims the value of leading and trailing whitespace.
            value = $.trim(value);

            // Cleaning the input.
            tagInput.val('');

            if (!isNew(value) || value == '') {
                return false;
            }

            var label = $(settings.onTagClicked ? '<a class="tagit-label"></a>' : '<span class="tagit-label"></span>').text(value);

            // create tag
            var tag = $('<li />')
                .addClass('tagit-choice')
                .addClass(additionalClass)
                .append(label)
                .append('<a class="close">x</a>');

            if (settings.singleField) {
                //TODO
                var tags = assignedTags();
                tags.push(value);
                updateSingleTagsField(tags);
            } else {
                var escapedValue = label.html();
                tag.append('<input type="hidden" style="display:none;" value="' + escapedValue + '" name="' + settings.itemName + '[' + settings.fieldName + '][]">');
            }

            if (settings.onTagAdded) {
                settings.onTagAdded(tag);
            }

            // insert tag
            tagInput.parent().before(tag);
        }
        function removeTag(tag) {
            if (settings.onTagRemoved) {
                settings.onTagRemoved(tag);
            }
            if (settings.singleField) {
                var tags = assignedTags();
                var removedTagLabel = tag.children('.tagit-label').text();
                tags = $.grep(tags, function(el){
                    return el != removedTagLabel;
                });
                updateSingleTagsField(tags);
            }
            tag.remove();
        }

        // maintaining chainability
        return this;
    };

})(jQuery);


