# -*- coding:utf-8 -*-

import textwrap
import requests
import json


class News:
    def __init__(self):
        self.news_list = None

    def update(self, api_id):
        try:
            response = requests.get(
                f"https://newsdata.io/api/1/latest?country=fr&category=top&domainurl=lefigaro.fr&apikey={api_id}"
            )
            response.raise_for_status()
            self.news_list = response.json()
            return self.news_list
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête : {e}")
            self.news_list = None
            return None
        except json.JSONDecodeError:
            print("Erreur de décodage JSON : la réponse n'est pas un JSON valide.")
            self.news_list = None
            return None

    def selected_title(self):
        list_news = []
        if self.news_list is None:
            print("Erreur : Aucune donnée de nouvelles disponible.  Appeler update() d'abord.")
            return []

        if "results" in self.news_list:
            for article in self.news_list["results"]:
                if "title" in article:
                    line = article["title"]
                    line = textwrap.wrap(line, width=60)
                    list_news.append(line)
                else:
                    print("Article sans titre trouvé.")
                    list_news.append(["Titre non disponible"])
            return list_news
        else:
            print("Erreur : 'results' n'est pas dans la réponse de l'API.")
            return []