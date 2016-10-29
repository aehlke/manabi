dojo.provide('reviews.CardStatsButton');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');
dojo.require('dijit.form.DropDownButton');
dojo.require('dijit.TooltipDialog');
//dojo.require('reviews.CardStats');

dojo.require('manabi');
dojo.require('reviews');


dojo.declare('reviews.CardStatsButton', [dijit.form.DropDownButton], {
    // Listens for card display broadcasts, and changes its behavior to 
    // load the stats for the newly displayed card when clicked.
    //
    // Disabled before any card is displayed.

    card: null,

    _cardDisplayedSubscriptionName: reviews.subscriptionNames.cardDisplayed,

    postCreate: function() {
        this.inherited(arguments);

        if (this.card == null) {
            this.set('disabled', true);
        }
        
    },

    startup: function() {

        // Subscribe to card display events
        this.subscribe(this._cardDisplayedSubscriptionName, dojo.hitch(this, function(data) {
            console.log('setting a new card');
            this.set('card', data.card);
        }));

        // Create our stats tooltip
        var dropDown = this.dropDown = new dijit.TooltipDialog({});
            //title:
        dropDown.startup();

        this.inherited(arguments);
    },

    _setCardAttr: function(/* Boolean */ card) {
        this.card = card;

        console.log('setCardAttr: ' + this.card==null);

        this.set('disabled', this.card == null);

        if (this.card) {
            this.dropDown.set('href', '/stats/cards/'+this.card.id+'/');
        };
    }


    //_set
});





