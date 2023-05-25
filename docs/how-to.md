# Comment se servir de cette extension?

1. Ouvrir l'application 3D Slicer.
2. Naviguer vers le module ICH_SEGMENTER_V2.

<img src="img/module-localization.png" width="300" height="400">

3. L'extension devrait ressembler à : 

<img src="img/module.png" width="550" height="425">

4. À l'aide des boutons "Get default directory" puis "Browse volume folder", sélectionner l'emplacement de vos fichiers `.nrrd`. Vous devriez voir vos fichiers apparaitre de cette manière.

<img src="img/case-list.png" width="450" height="400">

5. Remplir les champs "Annotator's name", "Degree" et "Revision step". 
6. Pour commencer à annoter les volumes, il faut appuyer sur le bouton "Start". Les boutons d'ajout de segments et de peinture deviendront disponibles par la suite. À tout moment, vous pouvez appuyer sur le bouton "Pause", les chronomètres s'arrêteront et vous ne pourrez pas activer les pinceaux jusqu'à ce que vous appuyiez sur "Restart" pour redémarrer les chronomètres. 
7. Il y a 3 modes de segmentation, soit ICH (intracerebral hemorrhage), IVH (intraventricular hemorrhage) et PHE (perihematomal edema). Il y a des outils additionnels sous l'onglet "Tools", tel qu'une efface, un outil de remplissage de petits trous et un outil pour lisser les bordures. De plus, on peut cacher le remplissage des segments afin de mieux visualiser les bordures.

<img src="img/tools.png" width="275" height="300">

8. Lorsque vous êtes satisfaits de vos annotations, appuyer sur "Save segmentation". 

### À noter: 
* Il n'y a pas d'option "undo" dans l'extension. Pour effectuer cette opération, il faut changer de module pour "Segment Editor", faire "undo" et puis retourner dans l'extension ICH_SEGMENTER_V2. 
* Les shortcuts de clavier sont uniquement disponibles dans l'onglet "Segment Editor". 
    * [Documentation Segment Editor](https://slicer.readthedocs.io/en/latest/user_guide/modules/segmenteditor.html)
    * <img src="img/shortcuts.png" width="225" height="125">
* Plus d'information : [RSNA ICH/IVH Annotation Guidelines](https://docs.google.com/presentation/d/1rNnL9DYoIV6n5kgpZJnEqtFvqLkHsEsz31M2za32U_s/edit#slide=id.g221166f35e0_0_34)
