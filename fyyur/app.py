#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import os
import sys


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)

# connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres@localhost:5432/fyyur"

#----------------------------------------------------------------------------#
# Models. (Artist, Venue and Show )
#----------------------------------------------------------------------------#

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    venue = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(120))

    venues = db.relationship('Venue', secondary='shows')
    shows = db.relationship('Show', backref=('artists'))

    def Artist_Dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'genres': self.genres.split(','),  
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'venue': self.venue,
            'description': self.description,
        }
        
    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    talent = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(120))    
    
    artists = db.relationship('Artist', secondary='shows')
    shows = db.relationship('Show', backref=('venues'))

    def Venue_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'address': self.address,
            'phone': self.phone,
            'genres': self.genres.split(','),  
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'talent': self.talent,
            'description': self.description,
        }

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)

    venue = db.relationship('Venue')
    artist = db.relationship('Artist')

    def show_artist(self):
        return {
            'artist_id': self.artist_id,
            'artist_name': self.artist.name,
            'artist_image_link': self.artist.image_link,
            'date_time': self.date_time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def show_venue(self):
        return {
            'venue_id': self.venue_id,
            'venue_name': self.venue.name,
            'venue_image_link': self.venue.image_link,
            'date_time': self.date_time.strftime('%Y-%m-%d %H:%M:%S')
        }

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


pass


# Venues

@app.route('/venues')
def venues():
    venues = Venue.query.order_by(Venue.state, Venue.city).all()

    val = []
    dictionary = {}
    city = None
    state = None
    for venue in venues:
        All_venue = {
            'id': venue.id,
            'name': venue.name,
            'count_future_shows': len(list(filter(lambda x: x.date_time > datetime.today(),
                                                  venue.shows)))
        }

        if venue.city == city and venue.state == state:
             dictionary['venues'].append(All_venue)
        else:
            if city is not None:
                val.append(dictionary)
            dictionary['city'] = venue.city
            dictionary['state'] = venue.state
            dictionary['venues'] = [All_venue]

        city = venue.city
        state = venue.state

    val.append(dictionary)
    return render_template('pages/venues.html', areas=val)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_temp = request.form.get('search_temp')
    venues = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_temp))).all()

    values = []
    for venue in venues:
        val = {}
        val['id'] = venue.id
        val['name'] = venue.name
        val['count_future_shows'] = len(venue.shows)
        values.append(val)

    response = {}
    response['count'] = len(values)
    response['data'] = values

    return render_template('pages/search_venues.html',
                           results=response,
                           search_temp =request.form.get('search_temp', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    p_shows = list(filter(lambda x: x.start_time <
                             datetime.today(), venue.shows))
    future_shows = list(filter(lambda x: x.start_time >=
                                 datetime.today(), venue.shows))

    p_shows = list(map(lambda x: x.show_artist(), p_shows))
    future_shows = list(map(lambda x: x.show_artist(), future_shows))

    values = venue.Venue_dict()
    values['p_shows'] = p_shows
    values['future_shows'] = future_shows
    values['count_p_shows'] = len(p_shows)
    values['count_future_shows'] = len(future_shows)

    return render_template('pages/show_venue.html', venue=values)

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        val_genres = request.form.getlist('genres')
        venue.genres = ','.join(val_genres)
        venue.facebook_link = request.form['facebook_link']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' +
                  request.form['name'] + ' Could not be listed!')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id).Venue_dict()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)

    error = False
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        val_genres = request.form.getlist('genres')
        venue.genres = ','.join(val_genres)  
        venue.facebook_link = request.form['facebook_link']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  -------------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_temp = request.form.get('search_temp')
    results = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_temp))).all() 

    response = {}
    response['count'] = len(results)
    response['data'] = results

    return render_template('pages/search_artists.html',
                           results=response,
                           search_temp=request.form.get('search_temp', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)

    p_shows = list(filter(lambda x: x.date_time <
                             datetime.today(), artist.shows)) 
    future_shows = list(filter(lambda x: x.date_time >=
                                 datetime.today(), artist.shows))

    p_shows = list(map(lambda x: x.show_venue(), p_shows))
    future_shows = list(map(lambda x: x.show_venue(), future_shows)) 

    All = artist.Artist_Dict()
    All['p_shows'] = p_shows
    All['future_shows'] = future_shows
    All['count_p_shows'] = len(p_shows)
    All['count_future_shows'] = len(future_shows)
    return render_template('pages/show_artist.html', artist=All)


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id).Artist_Dict()

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        val_genres = request.form.getlist('genres')
        artist.genres = ','.join(val_genres)
        artist.website = request.form['website']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.description = request.form['description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            return redirect(url_for('server_error'))
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    error = False
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website = request.form['website']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.description = request.form['description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        return render_template('pages/home.html')


@app.route('/shows')
def shows():
    shows = Show.query.all()

    All = []
    for show in shows:
        All.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'date_time': show.date_time.isoformat()
        })

    return render_template('pages/shows.html', shows=All)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        show = Show()
        show.artist_id = request.form['artist_id']
        show.venue_id = request.form['venue_id']
        show.date_time = request.form['date_time']
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An Error occurred , Show could not be listed.')
        else:
            flash('Show was successfully listed')
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

