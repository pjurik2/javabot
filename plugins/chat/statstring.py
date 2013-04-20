#The Diablo II statstring parsing within this module makes use of findings by
#iago, DarkMinion, and RealityRipple, among others

from pbuffer import debug_output

long_name = {'SSHR': 'Starcraft Shareware',
             'JSTR': 'Starcraft Japanese',
             'STAR': 'Starcraft',
             'SEXP': 'Starcraft Broodwar',
             'DSHR': 'Diablo Shareware',
             'DRTL': 'Diablo I',
             'D2DV': 'Diablo II',
             'D2XP': 'Diablo II: Lord of Destruction',
             'W2BN': 'Warcraft II: Battle.net Edition',
             'WAR3': 'Warcraft III',
             'W3XP': 'Warcraft III: The Frozen Throne'}

titles = ['Sir', 'Lord', 'Baron', 'Dame', 'Lady', 'Baroness', #MMMFFF normal
          'Count', 'Duke', 'King', 'Countess', 'Duchess', 'Queen', #MMMFFF hardcore
          'Slayer', 'Champion', 'Patriarch', 'Destroyer', 'Conquerer',
          'Guardian', 'Matriarch']

classes_d1 = ['Warrior', 'Rogue', 'Sorcerer', 'Unknown Class']
classes = ['Amazon', 'Sorceress', 'Necromancer', 'Paladin',
           'Barbarian', 'Druid', 'Assassin', 'Unknown Class']

helms = {4: 'Cap', 57: 'Cap', 5: 'Skullcap', 58: 'Skullcap', 6: 'Helm',
         59: 'Helm', 7: 'Fullhelm', 60: 'Fullhelm', 8: 'Greathelm',
         61: 'Greathelm', 10: 'Mask', 63: 'Mask', 40: 'Bonehelm',
         82: 'Bonehelm', 89: 'Fanged helm', 90: 'Warhelm', 91: 'Winged Helm',
         255: 'No helm (Circlet?)'}

weapons = {4: 'Hatchet/Waraze', 5: 'Axe', 6: 'Large Axe 6', 7: 'Large Axe 7',
           8: 'Greate Axe', 9: 'Wand 9', 10: 'Wand 10', 11: 'Wand 11',
           12: 'Spiked Club', 13: 'Scepter', 14: 'Hammer', 15: 'Flail',
           16: 'Maul', 17: 'Short Sword', 18: 'Scimitar/Saber', 19: 'Warsword',
           20: 'Crystal Sword', 21: 'Sword 21', 22: 'Sword 22', 23: 'Sword 23',
           24: 'Sword 24', 25: 'Dagger', 26: 'Dirk/Kris', 27: 'Unk 27',
           28: 'Unk 28', 29: 'Unk 29', 30: 'Spear', 31: 'Trident', 32: 'Spetum',
           33: 'Pike', 34: 'Bardiche/Halberd', 35: 'Sickle', 36: 'Poleaxe',
           37: 'Staff 37', 38: 'Staff 38', 39: 'Staff 39', 40: 'Staff 40',
           49: 'Unk 49', 50: 'Unk 50', 53: 'Orb', 56: 'Unk 56', 121: 'Unk 121',
           122: 'Unk 122', 123: 'Unk 123', 124: 'Unk 124', 125: 'Poison Potion',
           126: 'Fulmigating Potion', 127: 'Potion 3', 128: 'Potion 4',
           129: 'Potion 5'}

shields = {79: 'Small Shield', 80: 'Buckler', 81: 'Kite Shield',
           82: 'Tower Shield', 84: 'Bone Shield', 85: 'Spiked shield',
           92: 'Rondache', 94: 'Crown Shield'}


chan_flags = {0x02: 	'moderated',
              0x04: 	'restricted',
              0x08: 	'silent',
              0x10: 	'system',
              0x20: 	'product-specific',
              0x1000: 	'globally accessible'}

def kill_null(string):
    res = string.find('\0')
    if res == -1:
        return string
    else:
        return string[:string.find('\0')]

def safe_int(string):
    return int(kill_null(string).zfill(1))

def parse_chan_flags(flags):
    if (flags & 0x01) == 0x01:
        build = 'public'
    else:
        build = 'private'

    for k, v in chan_flags.iteritems():
        if (flags & k) == k:
            build += ', ' + v

    return build
    

def str_reverse(string):
    rev = reversed(string)
    build = ''

    for char in rev:
        build += char

    return build

def statstring(text):
    product = str_reverse(text[:4])
    results = {'product': product,
               'statstring': text}

    
    try:
        results['display'] = long_name[product]
    except KeyError:
        results['display'] = 'Unknown (%s)' % product
        return results


    if product in ['STAR', 'SEXP', 'JSTR', 'W2BN', 'SSHR']:
        results.update(stats_star(product, text[5:]))
        if results['wins'] != 0:
             results['display'] += ' (' +\
                                   str(results['wins']) + (results['wins'] == 1 and\
                                   ' win' or ' wins') +\
                                   (results['spawned'] and ', spawned)' or ')')

    elif product in ['DRTL', 'DSHR']:
        results.update(stats_diablo(product, text[5:]))
        if results['class_num'] != -1:
            results['display'] += ' (' +\
                                  results['class'] + \
                                  ', level ' + str(results['level']) + ')'
                             
    elif product in ['D2DV', 'D2XP']:
        results.update(stats_diablo2(product, text[4:]))
        if results['open']:
            results['display'] += ' (Open character)'
        else:
            results['display'] += ' (Level ' + str(results['level']) + ' ' +\
                                  results['class'] + ', ' +\
                                  results['title'] +\
                                  results['char_name'] + ' of ' +\
                                  results['realm'] + ' using a ' +\
                                  results['helm'] + ', ' +\
                                  results['weapon'] + ', and ' +\
                                  results['shield'] + ')'
            
    elif product in ['WAR3', 'W3XP']:
        results.update(stats_war3(product, text[5:]))

        if results['clan'] == '':
            if results['level'] != 0:
                results['display'] += ' (Level %s)' % str(results['level'])
        else:
            if results['level'] == 0:
                results['display'] += ' (Clan %s)' % results['clan']
            else:
                results['display'] += ' (Level %s of Clan %s)' % (str(results['level']),
                                                                  results['clan'])

    results['display'] += '.'
    return results
        

def stats_star(product, text):
    field = text.split(' ')

    try:
        return {'ladder_rating': safe_int(field[0]),
                'ladder_rank': safe_int(field[1]),
                'wins': safe_int(field[2]),
                'spawned': bool(safe_int(field[3])),
                #'unknown': field[4],
                'high_ladder_rating': safe_int(field[5]),
                #'unknown': field[6],
                #'unknown': field[7],
                'icon': str_reverse(field[8])}
    except:
        return {'ladder_rating': 0,
                'ladder_rank': 0,
                'wins': 0,
                'spawned': False,
                #'unknown': field[4],
                'high_ladder_rating': 0,
                #'unknown': field[6],
                #'unknown': field[7],
                'icon': ''}

def stats_diablo(product, text):
    field = text.split(' ')
    try:
        char_class = classes_d1[safe_int(field[1])]
        
        return {'level': safe_int(field[0]),
                'class': char_class,
                'class_num': safe_int(field[1]),
                'dots': safe_int(field[2]),
                'strength': safe_int(field[3]),
                'magic': safe_int(field[4]),
                'dexterity': safe_int(field[5]),
                'vitality': safe_int(field[6]),
                'gold': safe_int(field[7]),
                #'unknown': field[8],
                }
    except: #You can't really trust these
        return {'level': 0,
                'class': 'Open character',
                'class_num': -1,
                'dots': 0,
                'strength': 0,
                'magic': 0,
                'dexterity': 0,
                'vitality': 0,
                'gold': 0}

def stats_war3(product, text):
    if text == '':
        return {'icon': '',
                'level': 0,
                'clan': ''}
    field = text.split(' ')

    res =  {'icon': str_reverse(field[0]),
            'level': safe_int(field[1]),
            'clan': ''}
    if len(field) == 3:
        clan = str_reverse(field[2].strip('\xFF\0 '))
        if len(clan) in range(1, 5):
            res['clan'] = clan
            

    return res

def stats_diablo2(product, text):
    if text == '':
        return {'open': True}
    field = text.split(',', 2)
    if len(field) < 3:
        return {'open': True}

    realm = field[0]
    char_name = field[1]
    text = field[2][2:]
    if len(text) < 29:
        return {'open': True}

    flags = ord(text[24])
    hardcore = bool(flags & 0x04)
    dead = bool(flags & 0x08)
    expansion = bool(flags & 0x20)

    char_class = ord(text[11]) - 1
    char_class = char_class > 6 and 7 or char_class
    
    gender = (char_class in [0, 1, 6]) and 'Female' or 'Male'
    class_name = classes[char_class]

    acts = (ord(text[25]) & 0x3E) >> 1

    level = acts / 5 - 1

    if level == -1:
        title = ''
    else:
        title_idx = level

        if expansion:
            title_idx += 12
            if hardcore:
                title_idx += 3
            else:
                if gender == 'Female' and level == 2:
                    title_idx += 4
        else:
            if gender == 'Female':
                title_idx += 3
            if hardcore:
                title_idx += 6

        title = titles[title_idx] + ' '

    helm_idx = ord(text[0])
    try:
        helm = helms[helm_idx]
    except KeyError:
        helm = 'No helm (' + str(helm_idx) + ')'

    weap_idx = ord(text[5])
    try:
        weapon = weapons[weap_idx]
    except KeyError:
        weapon = 'No weapon (' + str(weap_idx) + ')'

    shield_idx = ord(text[7])
    try:
        shield = shields[shield_idx]
    except KeyError:
        shield = 'No shield (' + str(shield_idx) + ')'

    if class_name == 'Unknown Class':
        icon = product
    else:
        if product == 'D2XP':
            icon = 'DX' + class_name[:2].upper()
        else:
            icon = 'D2' + class_name[:2].upper()
        

    return {'level': ord(text[23]),
            'ladder': not ord(text[28]) == 255,
            'class': class_name,
            'title': title,
            'hardcore': hardcore,
            'dead': dead,
            'expansion': expansion,
            'realm': realm,
            'char_name': char_name,
            'open': False,
            'gender': gender,
            'acts': acts,
            'helm': helm,
            'weapon': weapon,
            'shield': shield,
            'icon': icon
            }
