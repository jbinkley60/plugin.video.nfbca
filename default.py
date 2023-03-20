import urllib.request, urllib.error, urllib.parse, re, sys, http.cookiejar, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
#import simplejson as json
import json
from xbmcgui import ListItem

# plugin constants
version = "0.0.99b"
plugin = "nfbca - " + version

__settings__ = xbmcaddon.Addon(id='plugin.video.nfbca')
rootDir = __settings__.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = xbmcvfs.translatePath(rootDir)
settingsDir = __settings__.getAddonInfo('profile')
settingsDir = xbmcvfs.translatePath(settingsDir)
cacheDir = os.path.join(settingsDir, 'cache')

programs_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'programs.png')
topics_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'topics.png')
search_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'search.png')
next_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'next.png')

pluginhandle = int(sys.argv[1])

########################################################
## URLs
########################################################
API_URL = 'http://www.nfb.ca/api/v2/json/%sapi_key=0f40a3cd-f7a4-5518-b49f-b6dee4ab8148&platform=mobile_android'
SEARCHURL = 'search/%s/?search_keywords=%s&qte=200&at_index=%d&'
CHANNELLIST = 'channel/all/?'
#CHANNEL = 'channel/content/%s/?qte=24&at_index=%d&'
CHANNEL = 'channel/content/%s/?qte=200&at_index=%d&'
MEDIAINFO = 'film/get_info/%s/?'
FEATURED = 'pagefeature/all/%s?'

########################################################
## Modes
########################################################
M_DO_NOTHING = 0
M_BROWSE_CHANNELS = 10
M_BROWSE_CHANNEL_CONTENTS = 20
M_SEARCH = 30
M_PLAY = 40
M_FEATURED = 50

##################
## Class for items
##################
class MediaItem:
    def __init__(self):
        self.ListItem = ListItem()
        self.Image = ''
        self.Url = ''
        self.Isfolder = False
        self.Mode = ''
        
## Get URL
def getURL( url ):
    cj = http.cookiejar.LWPCookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2;)')]
    usock=opener.open(url)
    response=usock.read()
    usock.close()
    return response

# Save page locally
def save_web_page(url):
    f = open(os.path.join(cacheDir, 'docnet.html'), 'w')
    data = getURL(url)
    f.write(data)
    f.close()
    return data
    
# Read from locally save page
def load_local_page():
    f = open(os.path.join(cacheDir, 'docnet.html'), 'r')
    data = f.read()
    f.close()
    return data

# Read local json - Temporary
def load_local_json(filename):
    f = open(os.path.join(cacheDir, filename), 'r')
    data = f.read()
    f.close()
    return data

# Remove HTML codes
def cleanHtml( dirty ):
    clean = re.sub('&quot;', '\"', dirty)
    clean = re.sub('&#039;', '\'', clean)
    clean = re.sub('&#215;', 'x', clean)
    clean = re.sub('&#038;', '&', clean)
    clean = re.sub('&#8216;', '\'', clean)
    clean = re.sub('&#8217;', '\'', clean)
    clean = re.sub('&#8211;', '-', clean)
    clean = re.sub('&#8220;', '\"', clean)
    clean = re.sub('&#8221;', '\"', clean)
    clean = re.sub('&#8212;', '-', clean)
    clean = re.sub('&amp;', '&', clean)
    clean = re.sub("`", '', clean)
    clean = re.sub('<em>', '[I]', clean)
    clean = re.sub('</em>', '[/I]', clean)
    clean = re.sub('<strong>', '', clean)
    clean = re.sub('</strong>', '', clean)
    return clean

########################################################
## Mode = None
## Build the main directory
########################################################
def BuildMainDirectory():
    MediaItems = []
    main = [
        (__settings__.getLocalizedString(30000), topics_thumb, str(M_FEATURED), 'en'),
        (__settings__.getLocalizedString(30001), topics_thumb, str(M_FEATURED), 'fr')
        ]
    for name, thumbnailImage, mode, lang in main:
        Mediaitem = MediaItem()
        Url = ''
        Mode = mode
        Title = name
        Thumb = thumbnailImage
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mode) + "&lang=" + lang
        #Mediaitem.ListItem.setThumbnailImage(Thumb)
        Mediaitem.ListItem.setArt({'thumb': Thumb, 'icon': Thumb})
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
        
    addDir(MediaItems)
    # End of Directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def Featured(lang):
    # set content type so library shows more views and info
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    # Get featured homepage contents
    URL = API_URL % (FEATURED % lang)
    data = getURL(URL)
    #data = load_local_json('featured.json')
    items = json.loads(data)
    itemList = items['data']
    itemList = [item for item in itemList]
    MediaItems = []
    for item in itemList:
        Mediaitem = MediaItem()
        Title = item['title']
        Slug = item['film_slug']
        MedUrl = MEDIAINFO % Slug
        Url = API_URL % MedUrl
        Mediaitem.Image = item['img']
        Plot = cleanHtml(item['description'])
        Mediaitem.Mode = M_PLAY
        Title = Title.encode('utf-8')
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mediaitem.Mode) + "&name=" + urllib.parse.quote_plus(Title)
        Mediaitem.ListItem.setInfo('video', { 'Title': Title, 'Plot': Plot})
        Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.ListItem.setProperty('IsPlayable', 'true')
        #Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
    # One Mediaitem for Channels
    Mediaitem = MediaItem()
    Url = ''
    Mode = M_BROWSE_CHANNELS
    Title = __settings__.getLocalizedString(30012)
    Thumb = topics_thumb
    Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mode) + "&lang=" + lang
    Mediaitem.ListItem.setArt({'thumb': Thumb, 'icon': Thumb})
    Mediaitem.ListItem.setLabel(Title)
    Mediaitem.Isfolder = True
    MediaItems.append(Mediaitem)
    # One Mediaitem for Search
    Mediaitem = MediaItem()
    Url = ''
    Mode = M_SEARCH
    Title = __settings__.getLocalizedString(30013)
    Thumb = search_thumb
    Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mode) + "&lang=" + lang
    Mediaitem.ListItem.setArt({'thumb': Thumb, 'icon': Thumb})
    Mediaitem.ListItem.setLabel(Title)
    Mediaitem.Isfolder = True
    MediaItems.append(Mediaitem)
    addDir(MediaItems)

    # End of Directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    ## Set Default View Mode. This might break with different skins. But who cares?
    #xbmc.executebuiltin("Container.SetViewMode(503)")
    SetViewMode()
    
###########################################################
## Mode == M_BROWSE_CHANNELS
## BROWSE CHANNELS
###########################################################
def BrowseChannels(lang):   
    # set content type so library shows more views and info
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    # Get featured homepage contents
    URL = API_URL % CHANNELLIST
    #xbmc.log('NFBCA M_Browse_Channels URL: ' + str(URL), xbmc.LOGINFO)
    data = getURL(URL)
    #data = load_local_json('channels.json')
    items = json.loads(data)
    itemList = items['data']
    itemList = [item for item in itemList if item.get('language', '') == lang]
    MediaItems = []
    for item in itemList:
        Mediaitem = MediaItem()
        Title = item['title']
        Slug = item['slug']
        StartIndex = 0
        ChUrl = CHANNEL % (Slug, StartIndex)
        Url = API_URL % ChUrl
        Mediaitem.Image = item['thumbnail']
        Plot = cleanHtml(item['description'])
        Mediaitem.Mode = M_BROWSE_CHANNEL_CONTENTS
        Title = Title.encode('utf-8')
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mediaitem.Mode) + "&lang=" + lang
        Mediaitem.ListItem.setInfo('video', { 'Title': Title, 'Plot': Plot})
        #Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setArt({'thumb': Mediaitem.Image, 'icon': Mediaitem.Image})
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        Mediaitem.ListItem.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('GoUp', 'Action(ParentDir)')])
        MediaItems.append(Mediaitem)
    addDir(MediaItems)

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

    # End of Directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    ## Set Default View Mode. This might break with different skins. But who cares?
    #xbmc.executebuiltin("Container.SetViewMode(503)")
    SetViewMode()
    
    
###########################################################
## Mode == M_BROWSE_CHANNEL_CONTENTS
## BROWSE CONTENTS
###########################################################   
def Browse(url, lang):
    # set content type so library shows more views and info
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    # Get contents for given url
    #xbmc.log('NFBCA M_Browse_Channels_Content URL: ' + str(url), xbmc.LOGINFO)
    ItemsPerPage, StartIndex = re.compile('qte=(\d+)&at_index=(\d+)&').findall(url)[0]
    ItemsPerPageInt = int( ItemsPerPage )
    StartIndexInt = int( StartIndex )
    #URL = API_URL + HOMESLIDE
    data = getURL(url)
    #data = load_local_json('search.json')
    items = json.loads(data)
    ItemCount = int(items['data_length'])
    #xbmc.log('NFBCA M_Browse_Channels_Content Item count: ' + str(ItemCount), xbmc.LOGINFO)
    if ItemCount < 1:
        return
    itemList = items['data']
    itemList = [item for item in itemList]
    MediaItems = []
    for item in itemList:
        Mediaitem = MediaItem()
        Genre = item['genres']
        Year = item['year']
        Rating = item['rating']
        #Playcount = item['viewed']
        Director = item['director']
        Mpaa = item['pg_rating']
        Title = item['title']
        Aired = item['publish_start']
        Slug = item['slug']
        Duration = get_seconds(item['time'])
        MedUrl = MEDIAINFO % Slug
        Url = API_URL % MedUrl
        Mediaitem.Image = item['big_thumbnail']
        Plot = cleanHtml(item['description'])
        Mediaitem.Mode = M_PLAY
        Title = Title
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mediaitem.Mode) + "&name=" + urllib.parse.quote_plus(Title)
        Mediaitem.ListItem.setInfo('video', { 'Title': Title, 'Plot': Plot, 'Duration': Duration,
                                             'Year': Year, 'Aired': Aired[:10], 'dateadded': Aired,
                                             'Rating': Rating, "mediatype": 'movie',
                                             'Director': Director, 'Mpaa': Mpaa})
        #Mediaitem.ListItem.setThumbnailImage(Mediaitem.Image)
        Mediaitem.ListItem.setArt({'thumb': Mediaitem.Image, 'icon': Mediaitem.Image})
        Mediaitem.ListItem.setProperty('IsPlayable', 'true')
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.ListItem.addContextMenuItems([ ('Refresh', 'Container.Refresh'), ('GoUp', 'Action(ParentDir)')])
        MediaItems.append(Mediaitem)
    NextStart = StartIndexInt + ItemsPerPageInt
    if NextStart < ItemCount:
        # One Mediaitem for Channels
        Mediaitem = MediaItem()
        Url = url.replace('at_index='+StartIndex, 'at_index='+str(NextStart))
        Mode = M_BROWSE_CHANNEL_CONTENTS
        Title = __settings__.getLocalizedString(30014)
        Thumb = next_thumb
        Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mode) + "&name=" + urllib.parse.quote_plus(Title)
        #Mediaitem.ListItem.setThumbnailImage(Thumb)
        Mediaitem.ListItem.setArt({'thumb': Thumb, 'icon': Thumb})
        Mediaitem.ListItem.setLabel(Title)
        Mediaitem.Isfolder = True
        MediaItems.append(Mediaitem)
    # One Mediaitem for Channels
    Mediaitem = MediaItem()
    Url = ''
    Mode = M_BROWSE_CHANNELS
    Title = __settings__.getLocalizedString(30012)
    Thumb = topics_thumb
    Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mode) + "&lang=" + lang
    #Mediaitem.ListItem.setThumbnailImage(Thumb)
    Mediaitem.ListItem.setArt({'thumb': Thumb, 'icon': Thumb})
    Mediaitem.ListItem.setLabel(Title)
    Mediaitem.Isfolder = True
    MediaItems.append(Mediaitem)
    # One Mediaitem for Search
    Mediaitem = MediaItem()
    Url = ''
    Mode = M_SEARCH
    Title = __settings__.getLocalizedString(30013)
    Thumb = search_thumb
    Mediaitem.Url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(Url) + "&mode=" + str(Mode) + "&lang=" + lang
    #Mediaitem.ListItem.setThumbnailImage(Thumb)
    Mediaitem.ListItem.setArt({'thumb': Thumb, 'icon': Thumb})
    Mediaitem.ListItem.setLabel(Title)
    Mediaitem.Isfolder = True
    MediaItems.append(Mediaitem)
    addDir(MediaItems)

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # End of Directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    ## Set Default View Mode. This might break with different skins. But who cares?
    #xbmc.executebuiltin("Container.SetViewMode(503)")
    SetViewMode()
    
###########################################################
## Mode == M_PLAY
## Try to get a list of playable items and play it.
###########################################################
def Play(url):
    if url == None or url == '':
        return
    # Get contents for given url
    #URL = API_URL + HOMESLIDE
    data = getURL(url)
    #data = load_local_json('mediainfo.json')
    items = json.loads(data)
    #xbmc.log('ndbca JSON: ' + str(items), xbmc.LOGINFO)
    if len(data) < 133:
        #xbmc.log("ndbca can't play item " + str(len(data)), xbmc.LOGINFO)
        xbmcgui.Dialog().ok(__settings__.getLocalizedString(30324), "Unable to play selected video")
        return        
    item = items['data'].get('film', '')
    Genre = item['genres']
    Year = item['year']
    Rating = item['rating']
    #Playcount = item['viewed']
    Director = item['director']
    Mpaa = item['pg_rating']
    Title = item['title']
    HQ = item['mobile_urls_versions'].get('HQ', '')
    vanilla = item['mobile_urls_versions'].get('vanilla', '')
    if HQ:
        Url = HQ
    else:
        Url = vanilla
    Thumb = item['big_thumbnail']
    Plot = cleanHtml(item['description'])
    Title = Title.encode('utf-8')
    #listitem = ListItem(Title, iconImage=Thumb, thumbnailImage=Thumb)
    listitem = ListItem(Title)
    listitem.setArt({'thumb': Thumb, 'icon': Thumb})
    listitem.setInfo('video', { 'Title': Title, 'Plot': Plot,
                                             'Genre': Genre, 'Year': Year,
                                             'Rating': Rating, #'Playcount': Playcount,
                                             'Director': Director, 'Mpaa': Mpaa})
    listitem.setPath(Url)
    #vid = xbmcgui.ListItem(path=url)
    #xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(url, vid)
    #xbmc.executebuiltin("xbmc.PlayMedia("+url+")")
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

# Set View Mode selected in the setting
def SetViewMode():
    try:
        current_skin_name = xbmc.getSkinDir()
        #xbmc.log('Curent Skin Name : ' + str(current_skin_name), xbmc.LOGINFO)
        if 'confluence' in current_skin_name:
            if __settings__.getSetting('view_mode') == "1": # List
                xbmc.executebuiltin('Container.SetViewMode(502)')
            if __settings__.getSetting('view_mode') == "2": # Big List
                xbmc.executebuiltin('Container.SetViewMode(51)')
            if __settings__.getSetting('view_mode') == "3": # Thumbnails
                xbmc.executebuiltin('Container.SetViewMode(500)')
            if __settings__.getSetting('view_mode') == "4": # Poster Wrap
                xbmc.executebuiltin('Container.SetViewMode(501)')
            if __settings__.getSetting('view_mode') == "5": # Fanart
                xbmc.executebuiltin('Container.SetViewMode(508)')
            if __settings__.getSetting('view_mode') == "6":  # Media info
                xbmc.executebuiltin('Container.SetViewMode(504)')
            if __settings__.getSetting('view_mode') == "7": # Media info 2
                xbmc.executebuiltin('Container.SetViewMode(503)')
        #xbmc.log('SetViewMode : ' + __settings__.getSetting('view_mode'), xbmc.LOGINFO)
    except:
        xbmc.log('SetViewMode Failed: ' + __settings__.getSetting('view_mode' + str(url)), xbmc.LOGINFO)


# Search documentaries
def SEARCH(url, lang):

        if url is None or url == '':
            keyb = xbmc.Keyboard('', 'Search NFB')
            keyb.doModal()
            if (keyb.isConfirmed() == False):
                return
            search = keyb.getText()
            if search is None or search == '':
                return
            #search = search.replace(" ", "+")
            encSrc = urllib.parse.quote(search)
            SearchIndex = 0
            Surl = SEARCHURL % (lang, encSrc, SearchIndex)
            url = API_URL % Surl
            #xbmc.log('NFBCA SEARCH URL: ' + str(url), xbmc.LOGINFO)
        
        Browse(url, lang)

## Get Parameters
def get_params():
        param = []
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
                params = sys.argv[2]
                cleanedparams = params.replace('?', '')
                if (params[len(params) - 1] == '/'):
                        params = params[0:len(params) - 2]
                pairsofparams = cleanedparams.split('&')
                param = {}
                for i in range(len(pairsofparams)):
                        splitparams = {}
                        splitparams = pairsofparams[i].split('=')
                        if (len(splitparams)) == 2:
                                param[splitparams[0]] = splitparams[1]
        return param

def get_seconds(time_text):
    time_split = time_text.split()
    time_count = len(time_split)
    if time_split[1] == 'min' and time_count == 4:
        secs = (int(time_split[0]) * 60) + int(time_split[2])
    elif time_split[1] == 'min' and time_count == 2:
        secs = (int(time_split[0]) * 60)        
    else:
        secs = int(time_split[0])
    return(secs)

def addDir(Listitems):
    if Listitems is None:
        return
    Items = []
    for Listitem in Listitems:
        Item = Listitem.Url, Listitem.ListItem, Listitem.Isfolder
        Items.append(Item)
    handle = pluginhandle
    xbmcplugin.addDirectoryItems(handle, Items)
    #xbmcplugin.addDirectoryItem(handle=pluginhandle, url, listitem, isFolder)

if not os.path.exists(settingsDir):
    os.mkdir(settingsDir)
if not os.path.exists(cacheDir):
    os.mkdir(cacheDir)
                    
params = get_params()
url = None
name = None
mode = None
titles = None
lang = None
try:
        url = urllib.parse.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.parse.unquote_plus(params["name"])
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass
try:
        titles = urllib.parse.unquote_plus(params["titles"])
except:
        pass
try:
    lang = params['lang']
except:
    pass

xbmc.log( "Mode: " + str(mode), xbmc.LOGDEBUG)


if mode == None:
    BuildMainDirectory()
elif mode == M_DO_NOTHING:
    #print 'Doing Nothing'
    xbmc.log('Doing Nothing', xbmc.LOGINFO)
elif mode == M_SEARCH:
    SEARCH(url, lang)
elif mode == M_BROWSE_CHANNELS:
    BrowseChannels(lang)
elif mode == M_BROWSE_CHANNEL_CONTENTS:
    Browse(url, lang)
elif mode == M_PLAY:
    Play(url)
elif mode == M_FEATURED:
    Featured(lang)