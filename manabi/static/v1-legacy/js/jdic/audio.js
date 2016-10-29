dojo.provide('jdic.audio');
dojo.provide('jdic.audio.JDicAudioServer');
dojo.provide('jdic.audio.JDicAudioPlayer');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');

dojo.declare('jdic.audio.Server', null, { 
    constructor: function(base_url) {
        //  Summary:
        //      A simple wrapper around a JDIC audio file server. It just 
        //      provides the proper URLs for given Japanese vocab items.
        //  description:
        //      It takes one parameter:
        //          base_url:    The root URL of a HTTP file server - this
        //                       directory should contain all the MP3 files
        //                       with filenames of form:
        //                          [reading] - [expession/kanji].mp3
        //                       The URL must end with '/'
        this.base_url = base_url;

        /*if (kwArgs && kwArgs.url_encoding) {
            this.url_encoding = kwArgs.url_encoding;
        }*/
    },

    _filename: function(kanji, kana) {
        return encodeURIComponent(dojo.trim(kana)) + ' - ' + encodeURIComponent(dojo.trim(kanji)) + '.mp3';
    },

    fileUrl: function(kanji, kana) {
        //  Summary:
        //      Returns a URL corresponding to the MP3 file for the given 
        //      kana and kanji. This file may or may not exist, though.
        //      So catch 404 errors when using this function's return value.
        return this.base_url + this._filename(kanji, kana);
    },

    audioExists: function(proxyUrl, kanji, kana) {
        // Whether an audio file exists for the given kanji and kana.
        // proxyUrl takes a filename on our audio server, and 
        //
        // returns whether that file exists (to get around the 
        // same origin policy in browsers).
        var def = new dojo.Deferred();

        var content = { filename: this._filename(kanji, kana) };
        console.log(content);
        console.log(proxyUrl);

        dojo.xhrPost({
            url: proxyUrl,
            content: content,
            type: 'json',
            load: function(result) {
            console.log('loading exists def');
            console.log(result);
                def.callback(result.data);
            },
            error: def.errback
        });
        return def;
    }
    
});


dojo.declare('jdic.audio.Player', [dijit._Widget, dijit._Templated], {
    //  summary:
    //      A widget wrapper for the jPlayer plugin for jQuery,
    //      optimized to work with our JDicAudioServer.
    //
    //  audioServer: JDicAudioServer
    //  kana: String
    //  kanji: String

    templateString: dojo.cache('jdic', 'templates/JDicAudioPlayer.html'),

    audioServer: null,
    kana: '',
    kanji: '',
    src: '',
    autoplay: false,

    postCreate: function(){
        // Start out hidden, until the file begins to load.
        dojo.style(this.domNode, 'display', 'none');
    },
    
    startup: function(){
        //  summary
        //      Initializes the jPlayer plugin widget on this node.
        var node = this.jPlayerNode;

        this.src = this.audioServer.fileUrl(this.kanji, this.kana);

        
        // jQuery plugin instantiation
        $(document).ready(dojo.hitch(this, function() {
            $(node).jPlayer({
                ready: dojo.hitch(null, function(jdicAudioPlayer) {
                    var player = $(this).jPlayer('setMedia', {
                        mp3: jdicAudioPlayer.src
                    });
                    if (jdicAudioPlayer.autoplay) {
                        $(this).jPlayer('play');
                    };
                }, this),

                swfPath: dojo.moduleUrl('jdic', 'jPlayer').toString(),

                solution: 'html, flash'
            });
            $(node).bind($.jPlayer.event.error + '.jdic', function(event) {
                // Wait until the data has loaded to show the 
                // audio player. This lets us keep it hidden if 
                // the file does not exist.
            });

            dojo.style(this.domNode, 'visibility', 'hidden');
            dojo.style(this.domNode, 'display', 'block');

            var showWidget = dojo.hitch(this, function(event) {
                // are we actually playing yet?
                // If so, show the widget. We know it didn't 404.
                if (event.jPlayer.status.currentTime != 0) {
                    //dojo.style(this.domNode, 'display', 'block');
                    dojo.style(this.domNode, 'visibility', '');
                }
            });

            // Using ".jp-show" namespace so we can easily 
            // remove this event
            $(node).bind($.jPlayer.event.error + '.jdic', dojo.hitch(this, function(event){
                dojo.style(this.domNode, 'display', 'none');
            }));
            $(node).bind($.jPlayer.event.timeupdate + '.jdic', showWidget);

        }));
    },

    destroy: function(){
        $(this.jplayerNode).jPlayer('stop');
        $(this.jplayerNode).unbind('.jdic');
    }
});

/*dojo.ready(function(){
var s = new jdic.audio.Server('http://jdic.manabi.org/audio/');
var p = new jdic.audio.Player({audioServer: s, kana: 'きょう', kanji: '今日', autoplay:true}).placeAt('footer', 'last');
p.startup();
});*/
