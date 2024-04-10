from dash import Dash, html, dcc
import plotly.express as px

import dash_bootstrap_components as dbc


from collections import Counter
import pandas as pd
import requests
import glob
import json
# import emoji

with open('../data/emoji_to_name.json') as f:
    e2n = json.load(f)
    # Goddamn fe0fs - I need to fix this once and for all
    e2n['🤼🏻'] = 'people_wrestling'
    e2n['⛄️'] = 'snowman_without_snow'
    e2n["☕️"] = "hot_beverage"
    e2n['⚽️'] = "soccer_ball"
    #e2n['♍️'] = 'virgo'
    
with open('../data/name_to_emoji.json') as f:
    n2e = json.load(f)
        
with open('../data/supported_emoji.json') as f:
    valid_emoji = json.load(f)['supported_emoji']

with open('../data/supported_alts.json') as f:
    valid_alts = json.load(f)['supported_alts']

subcats = pd.read_csv('subcat_data.csv', index_col='emoji').to_dict()['subcat']

# Begin dashboard
app = Dash(__name__,
	external_stylesheets=[dbc.themes.CYBORG],
	title='Emoji Kitchen Twitter Bot Dashboard',
	)

def serve_layout():

	# Get bitly data
	bitly_token = 'token'
	headers = {'Authorization': f'Bearer {bitly_token}'}
	params = (('unit', 'hour'), ('units', '-1'))

	response = requests.get('https://api-ssl.bitly.com/v4/bitlinks/bit.ly/get_Gboard/clicks',
	                        headers=headers,
	                        params=params)

	b_clicks = pd.DataFrame(response.json()['link_clicks'])
	b_total = b_clicks.clicks.sum()

	response = requests.get('https://api-ssl.bitly.com/v4/bitlinks/bit.ly/get_Gboard/countries',
	                        headers=headers,
	                        params=params)
	b_country = pd.DataFrame(response.json()['metrics'])
	b_country.columns = ['Country', 'Clicks']


	# Get log data
	logs = glob.glob('../logs/*.txt')
	data = pd.concat([pd.read_csv(i, sep='\t', header=None) for i in logs])
	data.columns = ['timestamp', 'event_type', 'sender', 'tweet', 'emoji_found', 'names_found', 'asset_returned']
	data.timestamp = data.timestamp.apply(pd.to_datetime)
	data['day'] = data.timestamp.apply(lambda x: str(x.date()))

	data.emoji_found = data.emoji_found.str.split(',')
	data.loc[data.emoji_found.isna(), 'emoji_found'] = ''
	data.names_found = data.names_found.str.split(',')
	data.loc[data.names_found.isna(), 'names_found'] = ''

	# Get follower data
	follower_data = pd.read_csv('follower_data.csv')


	click_fig = px.bar(b_clicks,
		x='date', y='clicks',
		height=300,
		title=f"Daily clicks sent to Gboard on Play Store (30 days):")
	bio_clicks_card = dbc.Card([dcc.Graph(id='bio_clicks', figure=click_fig)])

	click_fig.update_yaxes(title='Count')
	click_fig.update_xaxes(title=None)

	country_fig = px.bar(b_country,
		x='Country', y='Clicks',
		height=300,
		title=f'Clicks sent to Gboard on Play Store, per country (30 days):')
	country_clicks_card = dbc.Card([dcc.Graph(id='country_clicks', figure=country_fig)])

	country_fig.update_yaxes(title='Count')
	country_fig.update_xaxes(title=None)

	events_fig = px.bar(pd.DataFrame(data.event_type.value_counts()),
		height=300,
		title=f'Event types (total):')
	event_types_card = dbc.Card([dcc.Graph(id='event_types', figure=events_fig)])

	events_fig.update_yaxes(title='Count')
	events_fig.update_xaxes(title=None)
	events_fig.update_layout(showlegend=False)

	uf_data = pd.DataFrame(data.groupby('day').sender.nunique())
	users_fig = px.bar(uf_data,
		height=300,
		title=f'Daily unique users (total):')
	users_unique_card = dbc.Card([dcc.Graph(id='users_unique', figure=users_fig)])

	users_fig.update_layout(showlegend=False)
	users_fig.update_xaxes(title=None, tickformat='%d/%m/%y')
	users_fig.update_yaxes(title='Count')


	followers_fig = px.bar(follower_data,
		x='date',
		y='followers',
		height=300,
		title='Cumulative followers (daily):')
	followers_fig_card = dbc.Card([dcc.Graph(id='followers', figure=followers_fig)])

	followers_fig.update_xaxes(title=None)
	followers_fig.update_yaxes(title='Count')


	valid_found = Counter()
	invalid_found = Counter()

	for i in data.emoji_found.values:
	    for e in i:
	        if e2n.get(e) in valid_emoji or e2n.get(e) in valid_alts:
	            valid_found.update([e])
	        else:
	            invalid_found.update([e])
	            
	valid_found = pd.DataFrame([{'emoji':e, 'count':c} for e,c in valid_found.most_common() if c > 3][0:20])

	valid_found['is_alt?'] = valid_found.emoji.apply(lambda x: e2n.get(x) in valid_alts)
	valid_found['name'] = valid_found.emoji.apply(lambda x: e2n.get(x))
	valid_found['subcategory'] = valid_found.emoji.apply(lambda x: subcats.get(x, 'Missing Data'))

	invalid_found = pd.DataFrame([{'emoji':e, 'count':c} for e,c in invalid_found.most_common() if c > 3][0:20])
	invalid_found['name'] = invalid_found.emoji.apply(lambda x: e2n.get(x))
	invalid_found['subcategory'] = invalid_found.emoji.apply(lambda x: subcats.get(x, 'Missing Data'))


	valid_emoji_fig = px.bar(valid_found,
		x='emoji',
		y='count',
		height=300,
		hover_data=['emoji', 'name', 'count', 'is_alt?'],
		color='subcategory',
		category_orders={'emoji':valid_found.sort_values('count', ascending=False).emoji.values},
		title='Top 20 most requested supported emoji (total):')
	valid_emoji_fig_card = dbc.Card([dcc.Graph(id='valid_emoji', figure=valid_emoji_fig)])

	valid_emoji_fig.update_xaxes(title=None)
	valid_emoji_fig.update_yaxes(title='Count')

	invalid_emoji_fig = px.bar(invalid_found,
		x='emoji',
		y='count',
		color='subcategory',
		hover_data=['emoji', 'name', 'count'],
		category_orders={'emoji':invalid_found.sort_values('count', ascending=False).emoji.values},
		height=300,
		title='Top 20 most requested unsupported emoji (total):')
	invalid_emoji_fig_card = dbc.Card([dcc.Graph(id='invalid_emoji', figure=invalid_emoji_fig)])

	invalid_emoji_fig.update_xaxes(title=None)
	invalid_emoji_fig.update_yaxes(title='Count')

	daily_msg_fig = px.bar(data.groupby('day').timestamp.count(),
		height=300,
		title='Messages to bot (daily):')
	daily_msg_card = dbc.Card([dcc.Graph(id='daily_msg', figure=daily_msg_fig)])

	daily_msg_fig.update_xaxes(title=None)
	daily_msg_fig.update_yaxes(title='Count')
	daily_msg_fig.update_layout(showlegend=False)


	layout = dbc.Container(
		[
			dbc.Row([
				dbc.Card([
					html.H2(children=f'Emoji Kitchen Twitter Bot Dashboard'),
					html.P(children=f'Total followers: {follower_data.followers.iloc[-1]}'),
					html.P(children=f'Total unique users: {data.sender.nunique()}'),
					html.P(children=f'Total clicks sent to Gboard on Play Store: {b_total}'),
					html.P(children=f'Total messages to bot: {data.shape[0]}'),
					]),
				]),

			dbc.Row([
				dbc.CardGroup([
					dbc.Col(bio_clicks_card, md=6),
					dbc.Col(country_clicks_card, md=6),

					]),
				]),

			dbc.Row([
				dbc.CardGroup([
					dbc.Col(daily_msg_card, md=6),
					dbc.Col(event_types_card, md=6),				
					]),
				]),

			dbc.Row([
				dbc.CardGroup([
					dbc.Col(users_unique_card, md=6),
					dbc.Col(followers_fig_card, md=6),
					]),
				]),

			dbc.Row([
				dbc.CardGroup([
					dbc.Col(valid_emoji_fig_card, md=12),
					]),
				]),

			dbc.Row([
				dbc.CardGroup([
					dbc.Col(invalid_emoji_fig_card, md=12),
					]),
				]),
		])

	return layout

app.layout = serve_layout






if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')
