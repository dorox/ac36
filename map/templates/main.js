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
        height: '100%',
        width: '100%',
        videoId: '784D5bY0rW0',
    });
    playerMid = new YT.Player('playerMid', {
        height: '100%',
        width: '100%',
        videoId: '63Jv7jSxmms',
    });
    playerRight = new YT.Player('playerRight', {
        height: '100%',
        width: '100%',
        videoId: 'yAGyAgAOVR4',
    });
}