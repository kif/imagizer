Objectif:
=========

Imagizer est une suite composée de deux executables (selector et generator) 
et d'une bibliothèque (EXIF) qui permettent de classer, de trier, de nommer,
d'archiver, de sélectionner et finalement de produir des pages web statiques 
à partir des photos initiales. 

«Selector» est conçu pour tourner sur une station, il cherche toutes les
photos au format JPEG dans les sous répertoires, les classe en fonction de 
leur date, propose de les nommer ou de les selectionner.

«Generator» est un programme conçu pour tourner sur un serveur (web), il
fabrique les pages HTML et s'occupe de la connectivité entre les pages. C'est 
une variante du programme curator écrit par Martin Blais avec des templates 
optimisés. http://curator.sourceforge.net/ 
 

Première étape : selector
================

Au lancement de selector, toutes les photos trouvées dans le répertoire indiqué
(par défaut, le répertoire courant) sont renommées en fonction de leur date 
et de l'appareil d'origine. Ceci est particulirement utile pour manger les
photos provenant des divers appareils photos numériques sans cohérence dans les
noms des fichiers.

ATTENTION à ne pas lancer le programme sur un répertoire trop «en amont» car
selector vous renommerait toutes les photos qu'il a trouvé !!! Un message
d'avertissement vous permet de quitter le programme en cas de fausse
manipulation. Si ce message vous agace, l'option "-nowarning" court-circuite la
page d'avertissement.

Si un tag exif permet de définir l'orientation de la photo, celle-ci est tournée 
en fonction. Ceci est effectué avant l'affichage de l'interface et des photos.
Si vos photos ne possèdent pas ce drapeau, l'option "-noautorotate" permet
d'accélerer grandement l'étape de classement des photos.

On peut en suite tourner les photos si nécessaire et leur donner un titre.

options de selector :

-noautorotate : n'essaye pas de tourner automatiquement les photos, accélère la
vitesse de classement de plusieurs fois.

-nowarning : 

Ainsi que le répertoire de départ (à défaut, le répertoire courant)

Informations accessibles:
=========================

-APN:	marque et modèle.
-Photo:	résolution et taille, heure de prise, focale, ouverture, vitesse,
utilisation du flash et iso équivalente.

Actions possibles:
==================
Titre:		donne un titre à la photo. Ce titre sera ajouté aux
			données EXIF de la photo à la première action sur un
			bouton quel qu'il soit. Il est enregistré que la
			photo soit sélectionnée ou non.

Précédente:	permet de revenir à la photo prise immédiatement avant. (Page Up)

Suivante:	permet de passer à la photo prise immédiatement après. (Page Down)

Première:	permet de revenir à la photo la plus ancienne du répertoire traité. (Home)

Dernière:	permet de passer à la photo la plus récente du répertoire traité. (End)

Rotation à gauche: permet de tourner la photo de 90° dans le sens anti-horaire. (Ctrl + flèche gauche)

Rotation à droite: permet de tourner la photo de 90° dans le sens horaire. (Ctrl + flèche droite)

Sélectionner: ajoute la photo la liste des photos sélectrionnées.

Executer:	lance la copie de toutes les photos sélectionnées dans un répertoire
			"Selected" ainsi que la génération des vignettes (160x120) et des
			images pour l'affichage web (800x600).

Poubelle:	déplace les photos dans la poubelle, nommée "Trash"

Deuxième étape: generator
===============

Generator est un programme qui va réaliser une galerie de photo à partir du
répertoire "Selected". La seule option qu'il est nécessaire de lui fournir est
le répertoir de départ. Générator n'a pas besoin d'interface graphique et peut
donc etre lancé sur un serveur.


Dépendances
============
Python-2.3
Pythom-imaging (PIL)
python-glade2
exiftran






 
