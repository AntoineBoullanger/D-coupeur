VIDEO CLIP MAKER — DÉCOUPAGE UNIQUEMENT

Lancement depuis le dossier du projet :
python -m src.main

Prérequis :
pip install -r requirements.txt
FFmpeg et FFprobe doivent être installés et accessibles dans le PATH Windows.

Cette version ne fait ni montage, ni conversion verticale, ni flou, ni ajout de texte.
Elle coupe la vidéo source directement avec FFmpeg en copie de flux, généralement
beaucoup plus rapidement qu'un réencodage. Les points de coupe peuvent être légèrement
ajustés selon les images-clés de la vidéo.
