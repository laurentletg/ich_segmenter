# ICH-SEGMENTER_V2
* Extension de 3D Slicer 
* Segmentation manuelle d'hémorragies intra-cérébrales

### Étapes d'installation 
1. Télécharger [3D Slicer](https://download.slicer.org).  
2. Effectuer un `clone` de ce repository localement. 
3. Ouvrir l'application 3D Slicer. 
4. Activer le checkbox "Enable developer mode" dans `Edit -> Application Settings -> Developer -> Enable developer mode`. 
5. Ajouter le `path` local de ce repository dans `Edit -> Application Settings -> Modules -> Additional module paths`. 
    * Il se peut qu'il y ait des erreurs. On peut les constater dans la fenêtre `Python Console`. 
6. On retrouve le module sous `Examples -> ICH_SEGMENTER_V2`. 

### Trouble shooting 
* Il faut s'assurer d'avoir installé Qt. On peut suivre les 5 premières étapes de cette [marche à suivre pour Mac](https://web.stanford.edu/dept/cs_edu/resources/qt/install-mac). 
* S'il y a des modules qui sont manquants ("ModuleNotFoundError"), il faut les ajouter à l'environnement de 3D Slicer soit par les commandes suivantes dans la fenêtre `Python Console`: 
        `from slicer.util import pip_install`
        `pip_install("XYZ")` où on remplace `XYZ` par la librairie voulue

### Autres ressources
* Formation 3D Slicer : https://www.youtube.com/watch?v=QTEti9aY0vs&list=PLeaIM0zUlEqswa6Pskg9uMq15LiWWYP39 
* Documentation 3D Slicer : https://www.slicer.org/wiki/Documentation/Nightly/Training