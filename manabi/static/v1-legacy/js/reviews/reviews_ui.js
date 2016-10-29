// user interface functions for reviews

dojo.provide('reviews_ui');

dojo.require('reviews');
dojo.require('reviews.Session');
dojo.require('reviews.SessionOverDialog');



dojo.ready(function(){
    reviews_ui.reviewDialog = dijit.byId('reviews_fullscreenContainer');
    reviews_ui.sessionStarted = false;

    reviews_ui.session = null;
});


reviews_ui._showNoCardsDue = function() {
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
};



reviews_ui.showReviewOptions = function() {
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_noCardsDue').style.display = 'none';
    dojo.byId('reviews_emptyQuery').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
    reviews_beginReviewButton.set('disabled', false);
    reviews_beginEarlyReviewButton.set('disabled', true);
};


reviews_ui.openSessionOverDialog = function() {
    var sessionOverDialog = new reviews.SessionOverDialog({ session: this.session });
    sessionOverDialog.startup();
    sessionOverDialog.show();
};


reviews_ui.endSession = function() {
    reviews_ui.unsetKeyboardShortcuts();

    reviews_ui._unsubscribeFromSessionEvents();

    //show the page behind this
    dojo.byId('body_contents').style.display = '';
    dojo.byId('tabhead').style.display = '';

    dojo.byId('reviews_fullscreenContainer').style.display = 'none';
    //TODO-OLD fade out, less harsh
    //TODO-OLD show review session results
    //var reviewCount = reviews_ui.session.reviewCount;
    reviews_ui.session.endSession();

    if (this.session.reviewCount) {
        reviews_ui.openSessionOverDialog();

        // refresh the active page, in case it has due card counts etc
        manabi_ui.xhrReload();
    }

    reviews_ui.sessionStarted = false;
};


reviews_ui.displayNextIntervals = function(card) {
    //show a special message for card failures
    //FIXME but only for young card failures - mature cards should have an interval shown
    var now = new Date();
    dojo.byId('reviews_gradeNoneInterval').innerHTML = 'Review soon';
    dojo.byId('reviews_gradeHardInterval').innerHTML = card.humanizedNextInterval(reviews.grades.GRADE_HARD);
    dojo.byId('reviews_gradeGoodInterval').innerHTML = card.humanizedNextInterval(reviews.grades.GRADE_GOOD);
    dojo.byId('reviews_gradeEasyInterval').innerHTML = card.humanizedNextInterval(reviews.grades.GRADE_EASY);
};


reviews_ui.displayCard = function(card, showCardBack) {
    reviews_ui.cardBackVisible = false;
    reviews_ui.unsetCardBackKeyboardShortcuts();
    reviews_cardFront.set('content', card.front);
    dojo.byId('reviews_showCardBack').style.display = '';
    reviews_cardBack.set('content', '');
    reviews_cardBack.domNode.style.display = 'none';
    reviews_subfactPane.set('content', '');
    reviews_subfactPane.domNode.style.display = 'none';
    dojo.byId('reviews_gradeButtonsContainer').style.display = 'none';

    if (showCardBack) {
        // Happens when showing an undone card (and maybe other cases 
        // in the future).
        reviews_ui.showCardBack(card);
    } else {
        reviews_ui.setCardFrontKeyboardShortcuts();
        reviews_showCardBackButton.set('disabled', false);
        reviews_showCardBackButton.focus();

        // start timers
        reviews_ui.session.startCardTimer();
        reviews_ui.session.startQuestionTimer();
    }

    dojo.publish(reviews.subscriptionNames.cardDisplayed, [{
        card: card
    }]);
};

reviews_ui.goToNextCard = function() {
    //see if the session has already ended before moving on to the next card
    if (reviews_ui.sessionOverAfterCurrentCard || 
            (reviews_ui.session.reviewCount >= reviews_ui.session.cardLimit && reviews_ui.session.cardLimit)) {
        reviews_ui.endSession();
    } else {
        //disable the review buttons until the back is shown again
        dojo.query('.dijitButton', dojo.byId('reviews_gradeButtonsContainer')).forEach(function(node) {
            dijit.getEnclosingWidget(node).set('disabled', true);
        });
        //disable the card back button until the next card is ready
        reviews_showCardBackButton.set('disabled', true);
        
        var nextCardDef = reviews_ui.session.nextCard();
        nextCardDef.addCallback(function(nextCard) {
            if (nextCard) {
                //next card is ready
                reviews_ui.displayCard(nextCard);
            } else  {
                //out of cards on the server
                reviews_ui.endSession();
            }
        });
    }
};


reviews_ui.showCardBack = function(card) {
    reviews_showCardBackButton.set('disabled', true);
    reviews_ui.cardBackVisible = true;
    reviews_ui.unsetCardFrontKeyboardShortcuts();

    // Stop the question timer
    reviews_ui.session.stopQuestionTimer();

    // Enable the grade buttons
    dojo.query('.dijitButton', dojo.byId('reviews_gradeButtons')).forEach(function(node) {
        dijit.getEnclosingWidget(node).set('disabled', false);
    });

    dojo.byId('reviews_showCardBack').style.display = 'none';
    reviews_cardBack.set('content', card.back);
    reviews_cardBack.domNode.style.display = '';
    reviews_ui.displayNextIntervals(card);
    dojo.byId('reviews_gradeButtonsContainer').style.display = '';
    reviews_ui.reviewDialog.domNode.focus();
    reviews_ui.setCardBackKeyboardShortcuts();
};


reviews_ui.reviewCard = function(grade) {
    reviews_ui.session.reviewCurrentCard(grade).then(function(data) {
        // Enable the Undo button (maybe should do this before the def?)
        reviews_undoReviewButton.set('disabled', false);
        //FIXME anything go here?
    });
    reviews_ui.goToNextCard();
};


/*reviews_ui.displayNextCard = function() {
};*/


reviews_ui._disableReviewScreenUI = function(disable) {
    if (typeof disable == 'undefined') {
        disable = true;
    }
    dojo.query('.dijitButton', dojo.byId('reviews_fullscreenContainer')).forEach(function(item) {
        dijit.getEnclosingWidget(item).set('disabled', disable);
    });
};


reviews_ui.undo = function() {
    // disable review UI until the undo operation is finished
    reviews_ui._disableReviewScreenUI();

    var undoDef = reviews_ui.session.undo();

    undoDef.addCallback(function() {
        // Show the next card, now that the cache is cleared.
        // Also show its back.
        reviews_ui.goToNextCard();
        reviews_ui.showCardBack(reviews_ui.session.currentCard);

        // re-enable review UI
        reviews_ui._disableReviewScreenUI(false);

        // disable the undo button until next review submission
        reviews_undoReviewButton.set('disabled', true);
    });
};


reviews_ui.showReviewScreen = function() {
    //show the fullscreen reviews div
    dijit.byId('reviews_fullscreenContainer').domNode.style.display = '';

    //hide the page behind this
    dojo.byId('body_contents').style.display = 'none';
    dojo.byId('tabhead').style.display = 'none';

    //show the review screen and hide the end of review screen
    dojo.byId('reviews_reviewScreen').style.display = '';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';

    dijit.byId('reviews_fullscreenContainer').domNode.focus();
};


reviews_ui.isCardBackDisplayed = function() {
    //Returns true if the card's back side is shown
    return reviews_cardBack.domNode.style.display === '';
};


reviews_ui.unsetKeyboardShortcuts = function() {
    //unsets the keyboard shortcuts, `
    //no matter whether the card's front or back is currently displayed
    reviews_ui.unsetCardFrontKeyboardShortcuts();
    reviews_ui.unsetCardBackKeyboardShortcuts();
};

reviews_ui.setKeyboardShortcuts = function() {
    reviews_ui.unsetKeyboardShortcuts();
    if (reviews_ui.isCardBackDisplayed()) {
        reviews_ui.setCardBackKeyboardShortcuts();
    } else {
        reviews_ui.setCardFrontKeyboardShortcuts();
    }
};

reviews_ui.suspendCurrentCard = function() {
    reviews_ui.session.currentCard.suspend();
    reviews_ui.goToNextCard();
};

reviews_ui.cardFrontKeyboardShortcutConn = null;
reviews_ui.cardBackKeyboardShortcutConn = null;

reviews_ui.setCardBackKeyboardShortcuts = function() {
    reviews_ui.unsetCardBackKeyboardShortcuts(); //don't set twice
    //reviews_ui.cardBackKeyboardShortcutConn = dojo.connect(reviews_ui.reviewDialog, 'onKeyPress', function(e) {
    reviews_ui.cardBackKeyboardShortcutConn = dojo.connect(window, 'onkeypress', function(e) {
        switch(e.charOrCode) {
            case '0':
            case '1':
                reviews_ui.reviewCard(reviews.grades.GRADE_NONE);
                break;
            case '2':
                reviews_ui.reviewCard(reviews.grades.GRADE_HARD);
                break;
            case '3':
                reviews_ui.reviewCard(reviews.grades.GRADE_GOOD);
                break;
            case '4':
                reviews_ui.reviewCard(reviews.grades.GRADE_EASY);
                break;
        }
    });
};

reviews_ui.setCardFrontKeyboardShortcuts = function() {
  reviews_ui.unsetCardFrontKeyboardShortcuts(); //don't set twice
  reviews_ui.cardFrontKeyboardShortcutConn = dojo.connect(window, 'onkeypress', function(e) {
    var k = dojo.keys;
    switch(e.charOrCode) {
        case k.ENTER:
        case ' ':
            reviews_ui.showCardBack(reviews_ui.session.currentCard);
            dojo.stopEvent(e);
            break;
        //default:
    }
  });
};

reviews_ui.unsetCardFrontKeyboardShortcuts = function() {
    if (reviews_ui.cardFrontKeyboardShortcutConn) {
        dojo.disconnect(reviews_ui.cardFrontKeyboardShortcutConn);
    }
};

reviews_ui.unsetCardBackKeyboardShortcuts = function() {
    if (reviews_ui.cardBackKeyboardShortcutConn) {
        dojo.disconnect(reviews_ui.cardBackKeyboardShortcutConn);
    }
};

reviews_ui._subscribeToSessionEvents = function() {
    reviews_ui._eventSubscriptions = [];
    //session timer completion event (when the session timer has exceeded the session time limit)
    reviews_ui._eventSubscriptions.push(dojo.subscribe(reviews.subscriptionNames.sessionTimerOver, function(evt) {
        reviews_ui.sessionOverAfterCurrentCard = true;
    }));
}

reviews_ui._unsubscribeFromSessionEvents = function() {
    reviews_ui._eventSubscriptions.forEach(function(handle) {
        dojo.unsubscribe(handle);
    });
};

reviews_ui.startSession = function(args) { 
    // raise error (TODO-OLD we just ignore it for now) if the session is already
    // in progress
    if (reviews_ui.sessionStarted) {
        return;
    }

    manabi_ui.showLoader();

    var sessionArgs = {
        deckId: args.deckId || null,
        dailyNewCardLimit: 20, 
        cardLimit: args.sessionCardLimit || 0,
        timeLimit: args.sessionTimeLimit || 10,
        tagId: args.tag_id||null,
        earlyReview: args.earlyReview || false, 
        learnMore: args.learnMore || false,
        nextCardsForReviewUrl: '/flashcards/api/next-cards-for-review/',// rest-next_cards_for_review
        undoStackUrl: '/flashcards/api/next-cards-for-review/undo-stack/' // rest-review_undo_stack
    };

    _kmq.push(['record', 'Started review session', {deck: sessionArgs.deckId}]);

    reviews_ui.session = new reviews.Session(sessionArgs);
    reviews_ui.sessionStarted = true;
    reviews_ui.sessionOverAfterCurrentCard = false;
    reviews_undoReviewButton.set('disabled', true);
    reviews_ui.lastSessionArgs = dojo.clone(args);

    //start a review session with the server
    var session_def = reviews_ui.session.startSession();

    reviews_ui._subscribeToSessionEvents();

    //wait for the first cards to be returned from the server
    session_def.addCallback(function(initialCardPrefetch) {
        //show the first card
        reviews_ui.session.nextCard().then(dojo.hitch(null, function(initialCardPrefetch, nextCard) {
            manabi_ui.hideLoader();

            if (nextCard) {
                reviews_ui.showReviewScreen();

                //show the card
                reviews_ui.displayCard(nextCard);
            } else {
                //no cards are due
                //TODO-OLD show an error here, since this should not ever happen now in the new site design.
            }
        }, initialCardPrefetch));
    });
};

reviews_ui.submitReviewOptionsDialog = function(earlyReview, learnMore) {
    if (typeof earlyReview == 'undefined') {
        earlyReview = false;
    }
    if (typeof learnMore == 'undefined') {
        learnMore = false;
    }

    //hide this options screen
    //dojo.byId('reviews_reviewOptions').style.display = 'none';//({display: 'none'});

    //TODO-OLD add a loading screen

    //disable the submit button while it processes
    reviews_beginReviewButton.set('disabled', true);
    reviews_learnMoreButton.set('disabled', true);
    reviews_beginEarlyReviewButton.set('disabled', true);

    var decksGridItem = reviews_decksGrid.selection.getSelected()[0];
    var deckId = decksGridItem.id[0]; //TODO-OLD allow multiple selections
    var timeLimit = reviews_timeLimitInput.set('value');
    var cardLimit = reviews_cardLimitInput.set('value');
    //var dailyNewCardLimt = reviews_newCardLimitInput.set('value');

    //! var tag_id = reviews_filterByTagInput.set('value');
    //! if (reviews_filterByTagInput.set('displayedValue') == '') {
        //tag_id = '-1';
    //! }

    var args = {
        deckId: deckId,
        timeLimit: timeLimit,
        cardLimit: cardLimit,
        earlyReview: earlyReview,
        learnMore: learnMore
    };

    reviews_ui.startSession(args); //deckId, timeLimit, cardLimit, tag_id, earlyReview, learnMore); //, dailyNewCardLimt);
};



