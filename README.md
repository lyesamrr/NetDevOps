# NetDevOps
Ce projet démontre la mise en place d'une infrastructure réseau automatisée pour la gestion d'équipements Cisco, illustrant la transition du technicien qui tape des commandes vers l'architecte qui automatise.
#Automatisation Réseau Cisco

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Ansible](https://img.shields.io/badge/Ansible-2.9+-red.svg)](https://ansible.com)
[![Netmiko](https://img.shields.io/badge/Netmiko-4.0+-green.svg)](https://github.com/ktbyers/netmiko)

&gt; **Déployez une configuration complète sur un routeur Cisco en moins de 10 secondes**

Ce projet démontre l'automatisation réseau (NetDevOps) avec Python et Ansible pour gérer des infrastructures Cisco sans intervention manuelle.

##Démarrage Rapide

### Prérequis
```bash
# Installation des dépendances
pip install -r requirements.txt

# Pour Ansible
ansible-galaxy collection install cisco.ios
