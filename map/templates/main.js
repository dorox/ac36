var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// 3. This function creates an <iframe> (and YouTube player)
var playerLeft;
var playerMid;
var playerRight;

function onYouTubeIframeAPIReady() {
    console.log('YTapiready')
    playerLeft = new YT.Player('playerLeft', {
        videoId: 'WRraRPnBbXY',
    });
    playerMid = new YT.Player('playerMid', {
        videoId: 'Tyn-Vyuzrbc',
    });
    playerRight = new YT.Player('playerRight', {
        videoId: 'aJ_ewscxhRc',
    });
}