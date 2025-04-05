from flask import Flask, render_template, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.app import app

# Set template folder path for Vercel
app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'templates'))