Objectif:
=========

Imagizer est une suite compos�e de deux executables (selector et generator) 
et d'une biblioth�que (EXIF) qui permettent de classer, de trier, de nommer,
d'archiver, de s�lectionner et finalement de produir des pages web statiques 
� partir des photos initiales. 

�Selector� est con�u pour tourner sur une station, il cherche toutes les
photos au format JPEG dans les sous r�pertoires, les classe en fonction de 
leur date, propose de les nommer ou de les selectionner.

�Generator� est un programme con�u pour tourner sur un serveur (web), il
fabrique les pages HTML et s'occupe de la connectivit� entre les pages. C'est 
une variante du programme curator �crit par Martin Blais avec des templates 
optimis�s. http://curator.sourceforge.net/ 
 

Premi�re �tape : selector
================

Au lancement de selector, toutes les photos trouv�es dans le r�pertoire indiqu�
(par d�faut, le r�pertoire courant) sont renomm�es en fonction de leur date 
et de l'appareil d'origine. Ceci est particulirement utile pour manger les
photos provenant des divers appareils photos num�riques sans coh�rence dans les
noms des fichiers.

ATTENTION � ne pas lancer le programme sur un r�pertoire trop �en amont� car
selector vous renommerait toutes les photos qu'il a trouv� !!! Un message
d'avertissement vous permet de quitter le programme en cas de fausse
manipulation. Si ce message vous agace, l'option "-nowarning" court-circuite la
page d'avertissement.

Si un tag exif permet de d�finir l'orientation de la photo, celle-ci est tourn�e 
en fonction. Ceci est effectu� avant l'affichage de l'interface et des photos.
Si vos photos ne poss�dent pas ce drapeau, l'option "-noautorotate" permet
d'acc�lerer grandement l'�tape de classement des photos.

On peut en suite tourner les photos si n�cessaire et leur donner un titre.

options de selector :

-noautorotate : n'essaye pas de tourner automatiquement les photos, acc�l�re la
vitesse de classement de plusieurs fois.

-nowarning : 

Ainsi que le r�pertoire de d�part (� d�faut, le r�pertoire courant)

Informations accessibles:
=========================

-APN:	marque et mod�le.
-Photo:	r�solution et taille, heure de prise, focale, ouverture, vitesse,
utilisation du flash et iso �quivalente.

Actions possibles:
==================
Titre:		donne un titre � la photo. Ce titre sera ajout� aux
			donn�es EXIF de la photo � la premi�re action sur un
			bouton quel qu'il soit. Il est enregistr� que la
			photo soit s�lectionn�e ou non.

Pr�c�dente:	permet de revenir � la photo prise imm�diatement avant. (Page Up)

Suivante:	permet de passer � la photo prise imm�diatement apr�s. (Page Down)

Premi�re:	permet de revenir � la photo la plus ancienne du r�pertoire trait�. (Home)

Derni�re:	permet de passer � la photo la plus r�cente du r�pertoire trait�. (End)

Rotation � gauche: permet de tourner la photo de 90� dans le sens anti-horaire. (Ctrl + fl�che gauche)

Rotation � droite: permet de tourner la photo de 90� dans le sens horaire. (Ctrl + fl�che droite)

S�lectionner: ajoute la photo la liste des photos s�lectrionn�es.

Executer:	lance la copie de toutes les photos s�lectionn�es dans un r�pertoire
			"Selected" ainsi que la g�n�ration des vignettes (160x120) et des
			images pour l'affichage web (800x600).

Poubelle:	d�place les photos dans la poubelle, nomm�e "Trash"

Deuxi�me �tape: generator
===============

Generator est un programme qui va r�aliser une galerie de photo � partir du
r�pertoire "Selected". La seule option qu'il est n�cessaire de lui fournir est
le r�pertoir de d�part. G�n�rator n'a pas besoin d'interface graphique et peut
donc etre lanc� sur un serveur.


D�pendances
============
Python-2.3
Pythom-imaging (PIL)
python-glade2
exiftran






 
