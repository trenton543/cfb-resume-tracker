import json
import requests

def get_top_30_ap_poll():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings"
    res = requests.get(url).json()
    
    rankings_data = res.get('rankings', [])
    ap_poll = next((p for p in rankings_data if p.get('type') == 'ap'), None)
    
    if not ap_poll and rankings_data:
        ap_poll = rankings_data[0]
        
    teams = []
    if ap_poll:
        # Top 25
        for rank_info in ap_poll.get('ranks', []):
            team_data = rank_info.get('team', {})
            rank_num = rank_info.get('current', rank_info.get('rank', len(teams) + 1))
            
            # Clean display name (prevents "Miami Miami" duplication)
            location = team_data.get('location', '')
            nickname = team_data.get('nickname', '')
            full_name = team_data.get('displayName', f"{location} {nickname}".strip())
            
            teams.append({
                'rank': rank_num,
                'team_id': str(team_data.get('id', '')),
                'name': full_name,
                'logo': team_data.get('logo', '')
            })
            
        # Extend to Top 30 using "Others Receiving Votes"
        others = ap_poll.get('others', [])
        others_sorted = sorted(others, key=lambda x: x.get('points', 0), reverse=True)
        for team_info in others_sorted[:5]:
            team_data = team_info.get('team', {})
            location = team_data.get('location', '')
            nickname = team_data.get('nickname', '')
            full_name = team_data.get('displayName', f"{location} {nickname}".strip())
            
            teams.append({
                'rank': len(teams) + 1,
                'team_id': str(team_data.get('id', '')),
                'name': full_name,
                'logo': team_data.get('logo', '')
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
        opp_rank = rank_map.get(opp_id, 99) # 99 if outside top 30
        opp_abbr = opponent.get('team', {}).get('abbreviation', 'OPP')
        
        # Determine opponent rank tier
        if 1 <= opp_rank <= 10:
            tier = 'gold'
        elif 11 <= opp_rank <= 20:
            tier = 'silver'
        elif 21 <= opp_rank <= 30:
            tier = 'bronze'
        else:
            tier = 'black'
            
        if is_winner:
            badges.append({'type': 'win', 'tier': tier, 'opp': opp_abbr})
        else:
            badges.append({'type': 'loss', 'tier': tier, 'opp': opp_abbr})
            
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
