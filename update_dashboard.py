import json
import requests

def get_top_30_ap_poll():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings"
    res = requests.get(url).json()
    
    # Locate AP Poll
    ap_poll = next(p for p in res['rankings'] if p['type'] == 'ap')
    
    teams = []
    # Top 25
    for rank_info in ap_poll['ranks']:
        teams.append({
            'rank': rank_info['rank'],
            'team_id': rank_info['team']['id'],
            'name': rank_info['team']['nickname'],
            'location': rank_info['team']['location'],
            'logo': rank_info['team']['logo']
        })
        
    # Extend to Top 30 using "Others Receiving Votes"
    if 'others' in ap_poll:
        others_sorted = sorted(ap_poll['others'], key=lambda x: x.get('points', 0), reverse=True)
        for i, team_info in enumerate(others_sorted[:5]):
            teams.append({
                'rank': 26 + i,
                'team_id': team_info['team']['id'],
                'name': team_info['team']['nickname'],
                'location': team_info['team']['location'],
                'logo': team_info['team']['logo']
            })
            
    return teams

def build_rank_map(teams_list):
    return {t['team_id']: t['rank'] for t in teams_list}

def get_team_badges(team_id, rank_map):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/schedule"
    res = requests.get(url).json()
    
    badges = []
    for event in res.get('events', []):
        competition = event['competitions'][0]
        if not competition.get('status', {}).get('type', {}).get('completed'):
            continue  # Skip future games
            
        competitors = competition['competitors']
        my_team = next(c for c in competitors if c['team']['id'] == str(team_id))
        opponent = next(c for c in competitors if c['team']['id'] != str(team_id))
        
        is_winner = my_team.get('winner', False)
        opp_id = opponent['team']['id']
        opp_rank = rank_map.get(opp_id, 99) # 99 if outside top 30
        
        if is_winner:
            if 1 <= opp_rank <= 10:
                tier = 'gold'
            elif 11 <= opp_rank <= 20:
                tier = 'silver'
            elif 21 <= opp_rank <= 30:
                tier = 'bronze'
            else:
                tier = 'black'
            badges.append({'type': 'win', 'tier': tier, 'opp': opponent['team']['abbreviation']})
        else:
            badges.append({'type': 'loss', 'opp': opponent['team']['abbreviation']})
            
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
