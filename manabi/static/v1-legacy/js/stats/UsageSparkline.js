dojo.provide('stats.UsageSparkline');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');

dojo.require('manabi');


dojo.declare('stats.UsageSparkline', [dijit._Widget, dijit._Templated], {
    templateString: dojo.cache('stats', 'templates/UsageSparkline.html'),
    //widgetsInTemplate: true,

    deckId: null,

    //points: 12,
    days: 60,
    pointWidth: 4,
    _height: 20,
    barColor: '#437AA4',



    constructor: function(args) {
        dojo.safeMixin(this, args);
        this.data = null;
    },

    postCreate: function() {
        this.inherited(arguments);

        // download the stats
        var xhrArgs = {
            url: '/stats/graphs/daily_repetition_history.json',
            content: { days: this.days }
        };

        if (this.deckId) {
            xhrArgs.content = { deck: this.deckId };
        }

        this.data = manabi.xhrGet(xhrArgs);

        // width: 144px;
        // left:  -35px
        // points: 12,
        // pointWidth: 4
        // points*pointWidth = 48
        // width/points = 12
        // 35/(12*4)

        var graphWidth = (this.pointWidth * this.points) * 3 + 5;

        // crop amount for left side and right side, per
        // this is a magic ratio found by manual trial and inspection
        var xCrop = Math.round(32.0 / (12 * 4) * (this.points * this.pointWidth));

        var cropWidth = (graphWidth - (xCrop * 2));

        console.log(graphWidth);
        console.log(xCrop);

        dojo.query(this.cropNode).style({
        border:'solid 1px red',
            width: cropWidth + 'px',
            height: this._height + 'px',
        });
        dojo.query(this.containerNode).style({
            width: graphWidth + 'px',
            height: this._height + 'px',
            left: '-' + xCrop + 'px'
        });
    },

    startup: function() {
        this.inherited(arguments);

        // render the sparkline
        // (uses jQuery)
        $(dojo.hitch(this, function(){
            dojo.when(this.data, dojo.hitch(this, function(data) {
                console.log(data);
                $(this.containerNode).sparkline(data, { type: 'bar', barColor: this.barColor, height: this._height });
        //$('#compositebar').sparkline([4,1,5,7,9,9,8,7,6,6,4,7,8,4,3,2,2,5,6,7], { composite: true, fillColor: false, lineColor: 'red' });
                /*var chart = new Highcharts.Chart({
                    chart: {
                        renderTo: this.containerNode,
                        defaultSeriesType: 'column',
                        margin: [0, 0, 0, 0],
                        //borderWidth:1
                    },
                    title: { text: '' },
                    credits: { enabled: false },
                    xAxis: {
                        labels: { enabled: false }
                    },
                    yAxis: {
                        maxPadding: 0,
                        minPadding: 0,
                        endOnTick: false,
                        labels: { enabled: false }
                    },
                    legend: { enabled: false },
                    tooltip: { enabled: false },
                    plotOptions: {
                        column: {
                            pointPadding: 0,
                            groupPadding: 0
                        },
                        series: {
                            stacking: 'normal',
                            pointPadding: 0,
                            groupPadding: 0,
                            borderWidth: 0,
                            pointWidth: this.pointWidth,
                            shadow: false
                        }
                    },
                    series: data.series
                });*/
            }));
        }));
        
    }

});





