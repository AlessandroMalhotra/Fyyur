#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import (Flask, render_template, request, Response, flash, 
                  redirect, url_for, abort, jsonify)

from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database - Done 

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key = True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  start_time = db.Column(db.String(120), nullable = False)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False, unique=True)
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent= db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(200))
    show = db.relationship('Show', backref='venue', lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False, unique=True)
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(200))
    show = db.relationship('Show', backref='artist', lazy=True)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # loop over the venue list object and seperate the venues so that they are only listed under the same state and city
  locals =[]
  venues = Venue.query.all()
  places = Venue.query.distinct(Venue.city, Venue.state).all()

  for place in places:
    locals.append({
    'city': place.city,
    'state': place.state,
    'venues': [{
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
        } for venue in venues if
            venue.city == place.city and venue.state == place.state]
    })
  
  return render_template('pages/venues.html', areas=locals)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form.get('search_term', '')
  response = Venue.query.filter(Venue.name.ilike(f'%{search}%')).all()
  
  data = {}

  for results in response:
    data['count'] = len(response)

  return render_template('pages/search_venues.html', results=response, search_term=search, data=data)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  
  past = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
      Show.venue_id == venue_id, 
      Show.artist_id == Artist.id, 
      Show.start_time < str(datetime.now())
      ).\
      all()
  past_shows = []
  past_shows_count = 0
 
  upcoming = db.session.query(Artist, Show).join(Show).join(Venue).\
    filter(
      Show.venue_id == venue_id, 
      Show.artist_id == Artist.id, 
      Show.start_time > str(datetime.now())
      ).\
      all()
  upcoming_shows = []
  upcoming_shows_count = 0


  for artist, show in past:
      past_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.start_time)
      })
      past_shows_count += 1
  for artist, show in upcoming:
      upcoming_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': str(show.start_time)
      })
      upcoming_shows_count += 1

  return render_template('pages/show_venue.html', venue=venue , past_shows=past_shows, upcoming_shows=upcoming_shows,
  past_shows_count=past_shows_count, upcoming_shows_count=upcoming_shows_count)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, csrf_enabled=False)
  if form.validate_on_submit():
    try:
      new_venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data,
      phone=form.phone.data, genres=form.genres.data, image_link=form.image_link.data, website=form.website.data,
      facebook_link=form.facebook_link.data, seeking_talent=form.seeking_talent.data, seeking_description=form.seeking_description.data)
      
      db.session.add(new_venue)
      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully listed!')
    except ValueError as e:
      print(e)
      flash(' There was a error submitting' + form.name.data + 'Venue.')
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field +' ' + '|'.join(err))
    flash('Errors ' + str(message))
  return render_template('pages/home.html', form=form)


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  error = False
  try:
    venues = Venue.query.get.first_or_404(venue_id)
    db.session.delete(venues)
    db.session.commit()
    flash('The Venue has been successfully deleted!')
    return render_template('pages/home.html')
  except:
    flash('There was a problem deleting this Venue ')
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.order_by(Artist.id).all()

  return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = search_term=request.form.get('search_term', '')
  response = Artist.query.filter(Artist.name.ilike(f'%{search}%')).all()

  data = {}
  for i in response:
      data['count'] = len(response)
  
  return render_template('pages/search_artists.html', results=response, search_term=search , data=data)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
   artist = Artist.query.get(artist_id)
  
   return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form, csrf_enabled=False)
  artist = Artist.query.get(artist_id)

  if form.validate_on_submit():
    try:
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.address = form.address.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.image_link = form.image_link.data
      artist.facebook_link = form.facebook_link.data
      artist.seeking_talent = form.seeking_talent.data
      artist.seeking_description = form.seeking_description.data

      db.session.commit()
      flash('Artist ' + form.name.data + ' was successfully updated!')
    except ValueError as e:
      print(e)
      db.session.rollback()
    finally:
      db.session.close()
  else:
   flash(' There was a error submitting ' + form.name.data + 'Venue.')
   abort(500)

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form, csrf_enabled=False)
  venue = Venue.query.get(venue_id)
  if form.validate_on_submit():
    try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.image_link = form.image_link.data
      venue.facebook_link = form.facebook_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      
      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully updated!')
    except ValueError as e:
      print(e)
      flash(' There was a error submitting' + form.name.data + 'Venue.')
      db.session.rollback()
    finally:
      db.session.close()
  else:
   abort(500)
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, csrf_enabled=False)
  if form.validate_on_submit():
    try:
      new_artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data,
      phone=form.phone.data, genres=form.genres.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data,
      seeking_venue=form.seeking_venue.data, seeking_description=form.seeking_description.data)
      
      db.session.add(new_artist)
      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully committed!')
    except ValueError as e:
      print(e)
      flash(' There was a error submitting' + form.name.data + 'Venue.')
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field +' ' + '|'.join(err))
    flash('Errors ' + str(message))
  return render_template('pages/home.html')
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.join(Venue, Show.venue_id == Venue.id).join(Artist, Show.artist_id == Artist.id).all()

  data = []

  for show in shows:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': str(show.start_time)
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form, csrf_enabled=False)
  
  if form.validate_on_submit():
    try:
      show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully created!')
    except ValueError as e:
      print(e)
      db.session.rollback()
    finally:
      db.session.close()
  else:
   flash(' There was a error submitting the Show.')
   abort(500)

  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
