import json
import requests

def clean_team_name(team_data):
    location = team_data.get('location', '').strip()
    nickname = team_data.get('nickname', '').strip()
    display_name = team_data.get('displayName', '').strip()
    short_name = team_data.get('shortDisplayName', '').strip()
    
    if short_name and short_name != f"{location} {location}":
        return short_name
    elif location and nickname:
        if location.lower() in nickname.lower():
            return nickname
        if nickname.lower() in location.lower():
            return location
        return f"{location} {nickname}"
    return display_name or location or nickname or "Unknown Team"

def get_team_conference(team_id):
    if not team_id:
        return 'Other'
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}"
    try:
        res = requests.get(url).json()
        conf_name = res.get('team', {}).get('standingSummary', '')
        if 'SEC' in conf_name or 'Southeastern' in conf_name:
            return 'SEC'
        elif 'Big Ten' in conf_name:
            return 'Big Ten'
        elif 'Big 12' in conf_name:
            return 'Big 12'
        elif 'ACC' in conf_name or 'Atlantic Coast' in conf_name:
            return 'ACC'
    except Exception:
        pass
    return 'Other'

def get_top_30_ap_poll():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings"
    res = requests.get(url).json()
    
    rankings_data = res.get('rankings', [])
    ap_poll = next((p for p in rankings_data if p.get('type') == 'ap'), None)
    
    if not ap_poll and rankings_data:
        ap_poll = rankings_data[0]
        
    teams = []
    if ap_poll:
        for rank_info in ap_poll.get('ranks', []):
            team_data = rank_info.get('team', {})
            rank_num = rank_info.get('current', rank_info.get('rank', len(teams) + 1))
            team_id = str(team_data.get('id', ''))
            
            teams.append({
                'rank': rank_num,
                'team_id': team_id,
                'name': clean_team_name(team_data),
                'logo': team_data.get('logo', ''),
                'conference': get_team_conference(team_id)
            })
            
        others = ap_poll.get('others', [])
        others_sorted = sorted(others, key=lambda x: x.get('points', 0), reverse=True)
        for team_info in others_sorted[:5]:
            team_data = team_info.get('team', {})
            team_id = str(team_data.get('id', ''))
            teams.append({
                'rank': len(teams) + 1,
                'team_id': team_id,
                'name': clean_team_name(team_data),
                'logo': team_data.get('logo', ''),
                'conference': get_team_conference(team_id)
            })
            
    return teams

def build_rank_map(teams_list):
    return {t['team_id']: t['rank'] for t in teams_list if t.get('team_id')}

def get_team_badges(team_id, rank_map):
    if not team_id:
        return []
        
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/schedule"
    try:
        res = requests.get(url).json()
    except Exception:
        return []
    
    badges = []
    for event in res.get('events', []):
        competitions = event.get('competitions', [])
        if not competitions:
            continue
            
        competition = competitions[0]
        if not competition.get('status', {}).get('type', {}).get('completed'):
            continue
            
        competitors = competition.get('competitors', [])
        my_team = next((c for c in competitors if str(c.get('team', {}).get('id')) == str(team_id)), None)
        opponent = next((c for c in competitors if str(c.get('team', {}).get('id')) != str(team_id)), None)
        
        if not my_team or not opponent:
            continue
            
        is_winner = my_team.get('winner', False)
        opp_id = str(opponent.get('team', {}).get('id'))
        opp_rank = rank_map.get(opp_id, 99)
        opp_abbr = opponent.get('team', {}).get('abbreviation', 'OPP')
        
        # Extract Scores Safely
        my_score = my_team.get('score', '')
        if isinstance(my_score, dict):
            my_score = my_score.get('displayValue', '')
            
        opp_score = opponent.get('score', '')
        if isinstance(opp_score, dict):
            opp_score = opp_score.get('displayValue', '')
            
        score_str = f" ({my_score}–{opp_score})" if (my_score and opp_score) else ""
        
        if 1 <= opp_rank <= 10:
            tier = 'gold'
        elif 11 <= opp_rank <= 20:
            tier = 'silver'
        elif 21 <= opp_rank <= 30:
            tier = 'bronze'
        else:
            tier = 'black'
            
        if is_winner:
            badges.append({'type': 'win', 'tier': tier, 'opp': opp_abbr, 'score': score_str})
        else:
            badges.append({'type': 'loss', 'tier': tier, 'opp': opp_abbr, 'score': score_str})
            
    return badges

def generate_data():
    teams = get_top_30_ap_poll()
    rank_map = build_rank_map(teams)
    
    dashboard_data = []
    for team in teams:
        team['badges'] = get_team_badges(team['team_id'], rank_map)
        dashboard_data.append(team)
        
    with open('data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)

if __name__ == "__main__":
    generate_data()
