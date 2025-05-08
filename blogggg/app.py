from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user,logout_user # type: ignore
from flask import session, redirect, url_for, flash
from functools import wraps
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt # type: ignore
from flask_migrate import Migrate # type: ignore
import os
from datetime import datetime
from sqlalchemy import or_  # type: ignore
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
api = Api(app)
jwt = JWTManager(app)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Single database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_profile_complete = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default="user")

    def generate_password(self, password):
        self._password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self._password, password)

    def repr(self):
        return f'<User {self.username}>'

class TrendingBlog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    excerpt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    author_image = db.Column(db.String(300), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    read_time = db.Column(db.Integer, default=5)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer,default=0)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    claps = db.Column(db.Integer, default=0)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class ListModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    author = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), nullable=True)  
    read_time = db.Column(db.Integer, default=5)
    date = db.Column(db.DateTime, default=datetime.utcnow)  



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class UserRegisterResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        is_profile_complete=data.get("is_profile_complete")
        password = data.get('password')
        role = data.get('role', 'user')

        if not all([username, email, password]):
            return {"message": "Username, Email, and Password are required."}, 400

        if User.query.filter((User.email == email) | (User.username == username)).first():
            return {"message": "Username or Email already exists."}, 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role=role, is_profile_complete=is_profile_complete)

        db.session.add(user)
        db.session.commit()

        return {"message": "User registered successfully."}, 201
class TrendingBlogListAPI(Resource):
    def get(self):
        trending_blogs = TrendingBlog.query.order_by(TrendingBlog.date.desc()).all()
        return [{
            "id": blog.id,
            "title": blog.title,
            "excerpt": blog.excerpt,
            "content": blog.content,
            "category": blog.category if hasattr(blog, 'category') else "Uncategorized",
            "author": blog.author,
            "author_image": blog.author_image,
            "date": blog.date.strftime('%Y-%m-%d'),
            "read_time": blog.read_time,
            "likes": blog.likes,
            "comments": blog.comments,
            "views": blog.views,
            "image_path": blog.image_path if hasattr(blog, 'image_path') else None
        } for blog in trending_blogs], 200

# Add this to your API resource registration


class LoginResource(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"message": "No data provided."}, 400

        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(
                                                identity=user.username,
                                                additional_claims={"id": user.id, "role": user.role}
                                            )

            return {'access_token': access_token}, 200

        return {'message': 'Invalid credentials'}, 401


class UserProfileResource(Resource): 
    @jwt_required()
    def get(self):
        current_user_identity = get_jwt_identity()
        return {"message": f"Hello, {current_user_identity}"}


class BlogCreateAPI(Resource): 
    @jwt_required()
    def post(self):
        data = request.get_json()
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return {"message": "User not found"}, 404

        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        author = data.get('author', user.username)
        read_time = data.get('read_time', 5)

        if not all([title, content, category]):
            return {"message": "Missing fields"}, 400

        new_blog = BlogPost(
            title=title, content=content, category=category,
            author=author, read_time=read_time
        )
        db.session.add(new_blog)
        db.session.commit()

        return {"message": "Blog post created successfully"}, 201


class BlogListAPI(Resource): 
    def get(self):
        blogs = BlogPost.query.order_by(BlogPost.date.desc()).all()
        return [{
            "id": blog.id,
            "title": blog.title,
            "content": blog.content,
            "category": blog.category,
            "author": blog.author,
            "date": blog.date.strftime('%Y-%m-%d'),
            "read_time": blog.read_time,
            "image_path": blog.image_path
        } for blog in blogs], 200

class BlogDetailAPI(Resource): 
    def get(self, blog_id):
        blog = BlogPost.query.get_or_404(blog_id)
        return {
            "id": blog.id,
            "title": blog.title,
            "content": blog.content,
            "category": blog.category,
            "author": blog.author,
            "date": blog.date.strftime('%Y-%m-%d'),
            "read_time": blog.read_time,
            "image_path": blog.image_path
        }, 200
    

class AddCommentAPI(Resource):
    def post(self):
        data = request.get_json()

        author = data.get('author')
        comment = data.get('comment')
        post_id = data.get('post_id')

        if not author or not comment  or not post_id:
            return jsonify({"error": "Author and comment are required"}), 400

        conn = sqlite3.connect('site.db')
        c = conn.cursor()

        try:
            c.execute('''INSERT INTO comments (author, content) VALUES (?, ?)''', (author, comment))
            conn.commit()
            conn.close()

            return jsonify({"message": "Comment added successfully"}), 201

        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500


class DeleteBlogAPI(Resource): 
    def delete(self, blog_id):
        blog = BlogPost.query.get(blog_id)
        if not blog:
            return {"error": "Blog post not found"}, 404

        db.session.delete(blog)
        db.session.commit()

        return {"message": "Blog post deleted successfully", "blog_id": blog_id}, 200

class UpdateBlogAPI(Resource): 
    def put(self, blog_id):
        data = request.get_json()
        if not data:
            return {"error": "Invalid or missing JSON in request body"}, 400

        blog = BlogPost.query.get(blog_id)
        if not blog:
            return {"error": "Blog post not found"}, 404

        blog.title = data.get('title', blog.title)
        blog.content = data.get('content', blog.content)
        blog.category = data.get('category', blog.category)
        blog.author = data.get('author', blog.author)
        blog.read_time = data.get('read_time', blog.read_time)

        db.session.commit()

        return {"message": "Blog post updated successfully", "blog_id": blog.id}, 200


class AdminResource(Resource):
    @jwt_required()
    def get(self):
        claims = get_jwt()
        user_id = claims.get("id")
        role = claims.get("role")

        if role != "admin":
            return jsonify({"message": "Unauthorized"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found."}), 404

        return jsonify({"message": "Welcome, Admin!"})


class SomeProtectedResource(Resource): 
    @jwt_required()
    def get(self):
        claims = get_jwt()
        role = claims.get("role")
        if role != 'admin':
            return {"message": "You are not authorized to access this resource."}, 403

        return {"message": "Welcome, admin!"}, 200

TRENDING_BLOGS_DATA = [
    {"title": "The Future of AI in Everyday Life", "content": "AI is changing our lives...", "category": "Technology", "author": "John Doe", "read_time": 7, "author_image": "static/images/download1.jpeg", "likes": 150, "comments": 25},
    {"title": "10 Tips for a Healthier Lifestyle", "content": "Healthy living is easier...", "category": "Health", "author": "Jane Smith", "read_time": 5, "author_image": "static/images/download2.jpeg", "likes": 210, "comments": 18},
    {"title": "The Rise of Space Tourism", "content": "Space tourism is now real...", "category": "Science", "author": "Elon Star", "read_time": 6, "author_image": "static/images/download3.jpeg", "likes": 180, "comments": 32},
    {"title": "5 Hidden Travel Destinations in Europe", "content": "Escape the crowds...", "category": "Travel", "author": "Sarah Traveler", "read_time": 4, "author_image": "static/images/download4.jpeg", "likes": 120, "comments": 15},
    {"title": "The Power of Meditation", "content": "Daily meditation can help...", "category": "Health", "author": "Dr. Emily Calm", "read_time": 8, "author_image": "static/images/download5.jpeg", "likes": 250, "comments": 40},
    {"title": "How to Start Investing in Stocks", "content": "Stock investing is easy...", "category": "Finance", "author": "Michael Investor", "read_time": 9, "author_image": "static/images/download6.jpeg", "likes": 190, "comments": 28},
    {"title": "The Secret to Becoming a Great Writer", "content": "Writing is an art and skill...", "category": "Writing", "author": "Lisa Wordsmith", "read_time": 6, "author_image": "static/images/download7.jpeg", "likes": 160, "comments": 22},
    {"title": "Why Renewable Energy is the Future", "content": "Fossil fuels are fading...", "category": "Science", "author": "David Green", "read_time": 5, "author_image": "static/images/download8.jpeg", "likes": 220, "comments": 35},
    {"title": "The Evolution of Smartphones", "content": "Smartphones have evolved...", "category": "Technology", "author": "Kevin Tech", "read_time": 7, "author_image": "static/images/download9.jpeg", "likes": 170, "comments": 20},
    {"title": "How to Learn a New Language Fast", "content": "Mastering a language is easy...", "category": "Education", "author": "Anna Polyglot", "read_time": 6, "author_image": "static/images/download10.jpeg", "likes": 140, "comments": 17}
]


STATIC_COMMENTS_DATA = [
    {'author': 'Aastha', 'content': 'Good post', 'date': datetime.utcnow(), 'claps': 28},
    {'author': 'Radhika', 'content': 'A Very good Suggestion', 'date': datetime.utcnow(), 'claps': 19}
]


STATIC_ARTICLES_DATA = [
    {'title': 'First Article', 'content': 'This is the content of the first article.', 'author': 'Author One'},
    {'title': 'Second Article', 'content': 'Content for the second article goes here.', 'author': 'Author Two'}
]


STATIC_LISTS_DATA = [
    {'name': 'My First List', 'description': 'A list of interesting things.'},
    {'name': 'Another List', 'description': 'Some other items.'}
]

Topics = [
    "Technology", "Programming", "Data Science", "Writing",
    "Productivity", "Politics", "Climate", "Health",
    "Design", "Art", "Culture", "Business",
    "Science", "Food", "Travel", "Music",
    "Sports", "Fashion", "Education", "Photography"
]

def populate_db():
    with app.app_context():
        db.create_all()

        for blog_data in TRENDING_BLOGS_DATA:
            trending_blog = TrendingBlog(
                title=blog_data['title'],
                excerpt=blog_data.get('content', '')[:100] + '...',
                content=blog_data['content'],
                author=blog_data['author'],
                author_image=blog_data.get('author_image'),
                date=datetime.utcnow(), 
                read_time=blog_data['read_time'],
                likes=blog_data.get('likes', 0),
                comments=blog_data.get('comments', 0),
                views=0
            )
            db.session.add(trending_blog)


        for comment_data in STATIC_COMMENTS_DATA:
            comment = Comment(
                author=comment_data['author'],
                content=comment_data['content'],
                date=comment_data.get('date', datetime.utcnow()),
                claps=comment_data.get('claps', 0)
            )
            db.session.add(comment)


        for article_data in STATIC_ARTICLES_DATA:
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                author=article_data['author'],
                date_posted=datetime.utcnow()
            )
            db.session.add(article)


        for list_data in STATIC_LISTS_DATA:
            list_item = ListModel(
                name=list_data['name'],
                description=list_data.get('description'),
                date_created=datetime.utcnow()
            )
            db.session.add(list_item)

        db.session.commit()


def format_date(date_str):
    """Convert database timestamp to readable format"""
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    delta = datetime.now() - date

    if delta.days > 30:
        return f"{delta.days // 30} months ago"
    elif delta.days > 0:
        return f"{delta.days} days ago"
    elif delta.seconds > 3600:
        return f"{delta.seconds // 3600} hours ago"
    elif delta.seconds > 60:
        return f"{delta.seconds // 60} minutes ago"
    else:
        return "Just now"

# App Routes
@app.route('/')
def landing():
    return render_template("landing.html")

@app.route('/home')
def index():
    my_blogs = BlogPost.query.order_by(BlogPost.date.desc()).all()
    trending_posts = TrendingBlog.query.all()
    return render_template('index.html', my_blogs=my_blogs, trending_posts=trending_posts)



import traceback

@app.route('/api/blogs/create', methods=['POST'])
def create_blog():
    try:
        # Get data from the form
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")
        author = request.form.get("author")
        image = request.files.get("image")
        read_time_raw = request.form.get("read_time", 5)

        if not title or not content or not author:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            read_time = int(read_time_raw)
        except (ValueError, TypeError):
            read_time = 5

        image_path = None
        if image and image.filename:
            upload_dir = app.config.get('UPLOAD_FOLDER', 'static/uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, image.filename)
            image.save(filepath)
            image_path = os.path.join('uploads', image.filename)  

        new_post = BlogPost(
            title=title,
            content=content,
            category=category,
            author=author,
            read_time=read_time,
            image_path=image_path  
        )

        db.session.add(new_post)
        db.session.commit()

        return jsonify({"message": "Blog created successfully"}), 201

    except Exception as e:
        print(f"Error creating blog: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/blogs/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    blog = BlogPost.query.get(blog_id)
    if blog:
        return jsonify(blog.to_dict()), 200
    return jsonify({"error": "Blog not found"}), 404

# --- Update blog ---
@app.route('/blogs/<int:blog_id>/update', methods=['PUT'])
def update_blog(blog_id):
    blog = BlogPost.query.get(blog_id)
    if not blog:
        return jsonify({"error": "Blog not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    blog.title = data.get("title", blog.title)
    blog.content = data.get("content", blog.content)
    blog.category = data.get("category", blog.category)
    blog.read_time = data.get("read_time", blog.read_time)
    blog.image_path = data.get("image_path", blog.image_path)
    blog.author = data.get("author", blog.author)

    db.session.commit()
    return jsonify({"message": "Blog updated", "blog": blog.to_dict()}), 200



@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/submit_blog', methods=['POST'])
def submit_blog():
    title = request.form.get('title') or 'Untitled Blog'
    content = request.form.get('content') or 'No content provided.'
    category = request.form.get('category') or 'Uncategorized'
    author = request.form.get('author') or 'Damon'
    read_time = request.form.get('read_time', 5)

    image = request.files.get('image')
    image_path = None
    if image and image.filename:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_path = os.path.join('uploads', filename)

    new_blog = BlogPost(
        title=title,
        content=content,
        category=category,
        author=author,
        read_time=read_time,
        image_path=image_path,
        date_created=datetime.utcnow()
    )

    try:
        db.session.add(new_blog)
        db.session.commit()
        print("Blog post submitted successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")

    return redirect(url_for('index'))


@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    try:
        blogs = BlogPost.query.all()  
        blogs_data = [{
            "id": blog.id,
            "title": blog.title,
            "author": blog.author,
            "content": blog.content,
            "date": blog.date.strftime('%Y-%m-%d'),
            "read_time": blog.read_time,
        } for blog in blogs]
        return jsonify(blogs_data)
    except Exception as e:
        app.logger.error(f"Error fetching blogs: {e}")
        return jsonify({"error": "Internal Server Error"}), 500




@app.route('/blogs/<int:blog_id>/delete', methods=['DELETE'])
def delete_blog(blog_id):
    blog = BlogPost.query.get(blog_id)
    if blog:
        db.session.delete(blog)
        db.session.commit()
        return jsonify({"message": "Blog deleted successfully"}), 200
    else:
        return jsonify({"message": "Blog not found"}), 404



@app.route('/blog/<int:blog_id>')
def blog_detail(blog_id):
    blog = BlogPost.query.get_or_404(blog_id)
    return render_template('blog_detail.html', blog=blog)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return redirect(url_for('index'))

    trending_results = TrendingBlog.query.filter(
        or_(
            TrendingBlog.title.ilike(f'%{query}%'),
            TrendingBlog.content.ilike(f'%{query}%'),
            TrendingBlog.author.ilike(f'%{query}%')
        )
    ).all()

    user_blogs = BlogPost.query.filter(
        or_(
            BlogPost.title.ilike(f'%{query}%'),
            BlogPost.content.ilike(f'%{query}%'),
            BlogPost.category.ilike(f'%{query}%'),
            BlogPost.author.ilike(f'%{query}%')
        )
    ).order_by(BlogPost.date.desc()).all()

    return render_template(
        'search_results.html',
        query=query,
        trending_blogs=trending_results,
        user_blogs=user_blogs
    )

@app.route('/upload_trending_image/<int:blog_id>', methods=['POST'])
def upload_trending_image(blog_id):
    """Allows uploading an image for a trending blog post"""
    file = request.files.get('image')

    if not file or file.filename == '':
        return redirect(url_for('index'))

    filename = f"trending_{blog_id}.jpg"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    trending_blog = TrendingBlog.query.get(blog_id)
    if trending_blog:
        trending_blog.author_image = "uploads/" + filename
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/theme')
def themes():
    return render_template('theme.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({
            "username": user.username,
            "email": user.email,
            "role": user.role  
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            print(f"Received JSON data: {data}")  
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            confirm_password = data.get("confirm_password")
        else:
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

        if not username or not email or not password or not confirm_password:
            error_message = "Missing required fields."
            if request.is_json:
                return jsonify({"error": error_message}), 400
            flash(error_message, "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            error_message = "Passwords do not match!"
            if request.is_json:
                return jsonify({"error": error_message}), 400
            flash(error_message, "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            error_message = "Username already exists."
            if request.is_json:
                return jsonify({"error": error_message}), 400
            flash(error_message, "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            print("User successfully added to database.") 
        except Exception as e:
            print(f"Database error: {e}")  
            return jsonify({"error": "Database error, try again later"}), 500

        success_message = "User registered successfully."
        if request.is_json:
            return jsonify({"message": success_message, "user": username}), 200

        flash(success_message, "success")
        return redirect(url_for("login"))

    return render_template("signup.html")



@app.route('/forgot_password')
def forgot():
    return render_template("forgot_password.html")

@app.route('/profile/<username>', methods=['GET'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'username': user.username,
        'bio': user.bio,
        'location': user.location,
        'birth_date': str(user.birth_date) if user.birth_date else None,
        'profile_image': user.profile_image
    })



@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_profile_complete:
        return redirect(url_for("profile"))

    return render_template("dashboard.html", user=current_user)

user_profile_data = {
    'username': '',
    'email': '',
    'bio': '',
    'website': '',
    'profile_image': '',
    'badges': ''
}

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    global user_profile_data
    if request.method == 'POST':
        user_profile_data['bio'] = request.form.get("bio")
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                user_profile_data['profile_image'] = filename

        if 'new_badge' in request.form and request.form['new_badge'].strip():
            new_badge = request.form['new_badge'].strip()
            if user_profile_data['badges']:
                user_profile_data['badges'] += f', {new_badge}'
            else:
                user_profile_data['badges'] = new_badge

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('update_profile.html', user=current_user, profile=user_profile_data)

@app.route('/da')
def damon():
    comments = Comment.query.order_by(Comment.date.desc()).all()
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    lists = ListModel.query.all()

    post = {
        'member_only': True,
        'title': '10 Things To Do Instead of Watching NETFLIX!',
        'subtitle': 'Device-free Habit to increase your productivity and happiness.',
        'author': 'Ravneet Kaur',
        'publication': 'The Vibe',
        'read_time': '4 min read',
        'date': '2 days ago',
        'claps': 973,
        'comments': 19
    }

    return render_template('damon.html', post=post, comments=comments, articles=articles, lists=lists)

@app.route('/add_comment', methods=['POST'])
def add_comment():
    author = request.form.get('author')
    comment_content = request.form.get('comment')

    if author and comment_content:
        new_comment = Comment(author=author, content=comment_content)
        db.session.add(new_comment)
        db.session.commit()

    return redirect(url_for('damon'))

@app.route('/clap_comment/<int:comment_id>', methods=['POST'])
def clap_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.claps += 1
    db.session.commit()
    return redirect(url_for('damon'))

@app.route('/rec_topic')
def rec_topic():
    return render_template('rec_topic.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged Out Successfully","success")
    return redirect(url_for('index'))

@app.route('/badge')
@login_required
def badge():
    return render_template('badge.html')

def admin_required(func):
    @wraps(func)
    def wrapper_func(args,*kwargs):
        if current_user.role!="admin":
            flash ("You are not permitted to access this page","danger")
            return redirect(url_for('admin'))
        return func(args,*kwargs)
    return wrapper_func

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful! Please Complete Your Profile.", "success")
            if user.role=="admin":
                return redirect(url_for("badge"))
        else:
            flash("Access denied.", "danger")
            return redirect(url_for("admin")) 

    return render_template("admin_login.html") 

@app.route('/create_badge')
@login_required
@admin_required
def create_badge():
    return render_template('form.html')

# API Routes
api.add_resource(UserRegisterResource, '/api/register')
api.add_resource(LoginResource, '/api/login')
api.add_resource(BlogListAPI, '/api/blogs')
api.add_resource(BlogCreateAPI, '/api/blogs/create')
api.add_resource(BlogDetailAPI, '/api/blogs/<int:blog_id>')
api.add_resource(UserProfileResource, '/api/profile')
api.add_resource(AdminResource, '/api/admin')
api.add_resource(AddCommentAPI,'/add_comment')
api.add_resource(SomeProtectedResource, '/api/protected')
api.add_resource(UpdateBlogAPI, '/api/blog/update/<int:blog_id>')
api.add_resource(DeleteBlogAPI, '/api/blog/delete/<int:blog_id>')
api.add_resource(TrendingBlogListAPI, '/api/trending-blogs')


if __name__ == "__main__":
    populate_db()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host="127.0.0.1", port=5001, debug=True)