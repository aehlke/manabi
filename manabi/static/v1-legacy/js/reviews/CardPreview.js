dojo.provide('reviews.CardPreview');
dojo.provide('reviews.CardPreview.Production');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');


var format = function(tmpl, dict, formatters){
    // convert dict to a function, if needed
    var fn = dojo.isFunction(dict) ? dict : function(_, name) {
        return dojo.getObject(name, false, dict);
    };
    // perform the substitution
    return dojo.replace(tmpl, function(_, name) {
        var parts = name.split(":"),
            value = fn(_, parts[0]);
        if(parts.length > 1) {
            value = formatters[parts[1]](value, parts.slice(2));
        }
        return value;
    });
}

// custom formatters for format
var rubyScriptRegExp = /\s?(\S*?)\[(.*?)\]/g;
var rubyTemplate = '<span class="ezRuby" title="{reading}">{kanji}</span>';

var formatters = {
    furiganaize: function(text) {
        return text.replace(rubyScriptRegExp, function(match, kanji, reading){
            return format(rubyTemplate, {kanji: kanji, reading: reading});
        });
    },

    stripRubyText: function(text) {
        // TA[ta]beru becomes TAberu
        return text.replace(rubyScriptRegExp, function(match, kanji, reading){
            return kanji;
        });
    },

    stripKanji: function(reading) {
        // strips the kanji from a reading
        // TA[ta]beru becomes taberu
        return reading.replace(rubyScriptRegExp, function(match, kanji, reading){
            return reading;
        });
    }
};

dojo.declare('reviews.CardPreview._base', [dijit._Widget, dijit._Templated], {
    //  summary:

    templateString: dojo.cache('reviews', 'templates/CardPreview.html'),

    frontPrompt: '',
    formContainerNode: null,

    constructor: function(args) {
        this.fieldDefaults = {
            expression: '<span class="weak">expression</span>',
            meaning: '<span class="weak">meaning</span>',
            reading: '<span class="weak">reading</span>'
        };
        this.fields = dojo.clone(this.fieldDefaults);
        dojo.safeMixin(this, args);
    },

    postCreate: function(){
        //  summary
        //      Initializes the jPlayer plugin widget on this node.
        this.formContainerNode = dojo.query(this.domNode).closest('.fact_form_container')[0];
        this._bindFields();
        this.render();
        
        // connect to click events
        dojo.query(this.domNode).onclick(dojo.hitch(this, 'onClick'));

        this.inherited(arguments);
    },

    

    _bindFields: function() {
        // Binds callbacks to each input field in the form
        // to tell when their values change, so we can re-render.
        var that = this;
        var form = dijit.getEnclosingWidget(dojo.query('form', this.formContainerNode)[0]);

        for (var fieldName in this.fields) {
            dojo.query('.field_content.'+fieldName, this.formContainerNode).forEach(function(node){
                var field = dijit.getEnclosingWidget(node);
                var handler = function(fieldName, e){
                    var val = field.get('value');
                    that.fields[fieldName] = val ? val : that.fieldDefaults[fieldName];
                    that.render();
                };
                // use that.connect so that _Widget automatically unconnects on destroy
                var handler_ = dojo.hitch(this, handler, fieldName);
                that.connect(field, 'onChange', handler_);
                that.connect(field, 'onKeyUp', handler_);
                that.connect(field, 'value', handler_);
                that.connect(form, 'onSubmit', handler_);

                // force an initial refresh
                handler_(fieldName);
            });
        }
    },
    

    _renderReadingAndExpression: function() {
        // Hides the expression if the reading sans ruby text matches it
        var ret = format('<span class="reading">{reading:furiganaize}</span>', this.fields, formatters);
        if (dojo.trim(formatters.stripRubyText(this.fields.reading)) != dojo.trim(this.fields.expression)) {
            ret = format('<span class="expression">{expression}</span>', this.fields) + ret;
        }
        return ret;
    },

    render: function() {
        var front = this._renderFront();
        var back = this._renderBack();

        dojo.query(this.frontPromptNode).html(this.frontPrompt);
        dojo.query(this.frontNode).html(front);
        dojo.query(this.backNode).html(back);
    },

    onClick: function() {}
});




dojo.declare('reviews.CardPreview.Production', [reviews.CardPreview._base], {
    _renderFront: function() {
        return format('<span class="meaning">{meaning}</span>', this.fields, formatters);
    },

    _renderBack: function() {
        return this._renderReadingAndExpression();
    }
});


dojo.declare('reviews.CardPreview.Recognition', [reviews.CardPreview._base], {
    _renderFront: function() {
        return this._renderReadingAndExpression();
    },

    _renderBack: function() {
        return format('<span class="meaning">{meaning}</span>', this.fields, formatters);
    }
});


dojo.declare('reviews.CardPreview.KanjiReading', [reviews.CardPreview._base], {
    _renderFront: function() {
        return format('<span class="expression">{expression}</span>', this.fields, formatters);
    },

    _renderBack: function() {
        return format('<span class="reading">{reading:stripKanji}</span><span class="meaning">{meaning}</span>', this.fields, formatters);
    }
});

dojo.declare('reviews.CardPreview.KanjiWriting', [reviews.CardPreview._base], {
    _renderFront: function() {
        return format('<span class="reading">{reading:stripKanji}</span><span class="meaning">{meaning}</span>', this.fields, formatters);
    },

    _renderBack: function() {
        return format('<span class="expression">{expression}</span>', this.fields);
    }
});


