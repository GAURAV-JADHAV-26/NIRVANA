
from flask import Flask, request, redirect, session, render_template, jsonify, json, url_for
from flask_mail import Mail, Message
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from motor.motor_asyncio import AsyncIOMotorClient
import requests
import base64
import spotipy
import pymongo
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import shazamio
import sounddevice as sd
import soundfile as sf
import tempfile
import threading
import os
