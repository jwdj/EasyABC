dialog_background_colour = None # will be initialized at startup depending on system thema wx.Colour(245, 244, 235)

is_dark_mode = None  # Initialized after wx.App creation
default_lock_music_light_mode = False

default_style_color = {
    # Standard colors for the app
    'app_background':               '#F0F0F0', # Will be replaced by wx.SYS_COLOUR_FRAMEBK when needed
    
    # Music Score
    'music_background':             '#FFFFFF',
    'music_sepia_background':       '#F4ECD8', # Only used in dark mode
    'note_highlight_color':         '#FF7F3F',
    'note_highlight_follow_color':  '#CC00FF',

    # ABC Editor
    'editor_background':            '#FFFFFF',
    'editor_foreground':            '#131415',
    'editor_caret':                 '#000000',
    'editor_linenumber_bg':         '#F0F0F0',
    'editor_linenumber_fg':         '#646464',
    'editor_selection_bg':          '#A6CAF0',
    'editor_selection_fg':          '#000000',

    # ABC Syntax
    'style_default_color':          '#131415',
    'style_chord_color':            '#131415',
    'style_comment_color':          '#656E77',
    'style_specialcomment_color':   '#803378',
    'style_bar_color':              '#0000CC',
    'style_field_color':            '#B75501',
    'style_fieldvalue_color':       '#B75501',
    'style_embeddedfield_color':    '#B75501',
    'style_embeddedfieldvalue_color':'#B75501',
    'style_fieldindex_color':       '#000000',
    'style_string_color':           '#2F6F44',
    'style_lyrics_color':           '#51774e',
    'style_grace_color':            '#5A3700',
    'style_ornament_color':         '#015692',
    'style_ornamentplus_color':     '#015692',
    'style_ornamentexcl_color':     '#015692'
}

default_dark_style_color = {
    # Standard colors for the app
    'app_background':               '#1E1E1E',
    
    # Music Score
    'music_background':             '#1E1E1E',
    'music_sepia_background':       '#F4ECD8',
    'note_highlight_color':         '#FF4D4D',
    'note_highlight_follow_color':  '#66A3FF',
    
    # ABC Editor
    'editor_background':            '#1E1E1E',
    'editor_foreground':            '#E0E0E0',
    'editor_caret':                 '#FFFFFF',
    'editor_linenumber_bg':         '#262626',
    'editor_linenumber_fg':         '#969696',
    'editor_selection_bg':          '#284B73',
    'editor_selection_fg':          '#FFFFFF',

    # ABC Syntax
    'style_default_color':          '#E0E0E0',
    'style_chord_color':            '#E0E0E0',
    'style_comment_color':          '#9DA5AD',
    'style_specialcomment_color':   '#D19ED1',
    'style_bar_color':              '#6699FF',
    'style_field_color':            '#FFB366',
    'style_fieldvalue_color':       '#FFB366',
    'style_embeddedfield_color':    '#FFB366',
    'style_embeddedfieldvalue_color':'#FFB366',
    'style_fieldindex_color':       '#FFFFFF',
    'style_string_color':           '#7FBF8F',
    'style_lyrics_color':           '#8FBF8F',
    'style_grace_color':            '#CFAA7F',
    'style_ornament_color':         '#6EB5FF',
    'style_ornamentplus_color':     '#6EB5FF',
    'style_ornamentexcl_color':     '#6EB5FF'
}

def get_default_style_color():
    """Retrieve default colors according to current appearance mode"""
    active_defaults = default_dark_style_color if is_dark_mode else default_style_color
    return active_defaults

def get_effective_style_color(settings):
    """Retrieve complete set of customize color for current appearance mode or default"""
    effective = {}
    if is_dark_mode:
        for key, default_val in default_dark_style_color.items():
            effective[key] = settings.get(f"{key}_dark", default_val)
    else:
        for key, default_val in default_style_color.items():
            effective[key] = settings.get(key, default_val)
    return effective

def get_effective_color(settings, key):
    """Retrieve one customize color or fall back to the default one."""
    if is_dark_mode:
        return settings.get(f"{key}_dark", default_dark_style_color.get(key))
    return settings.get(key, default_style_color.get(key))

def get_music_background(settings):
    """Retrieve current background color of the music score."""
    lock_music_light = settings.get('lock_music_light_mode', default_lock_music_light_mode)
    
    if lock_music_light and is_dark_mode:
        bg_hex = get_effective_color(settings,'music_sepia_background')
        return bg_hex

    bg_hex = get_effective_color(settings,'music_background')
    return bg_hex

def convert_raw_svg_color(settings, color):
    """From an SVG color (ex: 'black' or '#000000') returns the colors depending on dark mode."""
    lock_music_light = settings.get('lock_music_light_mode', default_lock_music_light_mode)
    if not is_dark_mode or lock_music_light:
        return color
        
    color_lower = color.lower().strip()
    
    # Foreground elements
    if color_lower in ('black', '#000000', '#000', '#2d2d2d'):
        return settings.get('style_default_color_dark', default_dark_style_color['style_default_color']) # '#E0E0E0'
        
    # Background elements
    if color_lower in ('white', '#ffffff', '#fff', '#e5e5e5'):
        return settings.get('music_background_dark', default_dark_style_color['music_background']) # '#1E1E1E'
        
    return color
