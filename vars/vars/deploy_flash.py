#!/usr/bin/env python3
"""
NetDevOps - Script de Déploiement Flash
Configure automatiquement VLANs, IPs et SSH sur équipements Cisco
Usage: python deploy_flash.py --device Router-Core-01
"""

import yaml
import argparse
import sys
from datetime import datetime
from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


def load_variables():
    """Charge les variables depuis les fichiers YAML"""
    base_path = Path(__file__).parent.parent
    
    with open(base_path / "vars" / "devices.yml", "r") as f:
        devices_data = yaml.safe_load(f)
    
    with open(base_path / "vars" / "vlans.yml", "r") as f:
        vlans_data = yaml.safe_load(f)
    
    return devices_data["devices"], vlans_data


def find_device(devices, name):
    """Trouve un device par son nom ou IP"""
    for device in devices:
        if device["name"] == name or device["ip"] == name:
            return device
    return None


def generate_vlan_commands(vlans_data):
    """Génère les commandes de configuration VLAN"""
    commands = ["configure terminal"]
    
    for vlan in vlans_data["vlans"]:
        commands.extend([
            f"vlan {vlan['id']}",
            f" name {vlan['name']}",
            "exit"
        ])
    
    return commands


def generate_ssh_commands(vlans_data):
    """Génère les commandes de configuration SSH"""
    ssh = vlans_data["ssh"]
    commands = [
        "configure terminal",
        f"ip domain-name {ssh['domain_name']}",
        "crypto key generate rsa",
        str(ssh["key_length"]),
        "ip ssh version 2",
        "line vty 0 15",
        " transport input ssh",
        " login local",
        "exit"
    ]
    return commands


def generate_interface_commands(vlans_data):
    """Configure les interfaces SVI pour les VLANs"""
    commands = ["configure terminal"]
    
    for vlan in vlans_data["vlans"]:
        commands.extend([
            f"interface vlan {vlan['id']}",
            f" description Gateway for {vlan['name']}",
            f" ip address {vlan['gateway']} 255.255.255.0",
            " no shutdown",
            "exit"
        ])
    
    return commands


def deploy_configuration(device_info, vlans_data, dry_run=False):
    """Déploie la configuration complète sur l'équipement"""
    
    connection_params = {
        "device_type": device_info["device_type"],
        "host": device_info["ip"],
        "username": device_info["username"],
        "password": device_info["password"],
        "port": device_info.get("port", 22),
        "timeout": 30,
        "conn_timeout": 30
    }
    
    print(f"\n{'='*60}")
    print(f" DÉPLOIEMENT: {device_info['name']} ({device_info['ip']})")
    print(f"{'='*60}")
    
    if dry_run:
        print(" MODE SIMULATION (Dry Run)")
        commands = generate_vlan_commands(vlans_data)
        print("\nCommandes VLAN générées:")
        for cmd in commands:
            print(f"  > {cmd}")
        return True
    
    try:
        print(" Connexion en cours...")
        connection = ConnectHandler(**connection_params)
        
        # 1. Configuration des VLANs
        print("\n Étape 1/3: Configuration des VLANs...")
        vlan_commands = generate_vlan_commands(vlans_data)
        output = connection.send_config_set(vlan_commands)
        print(f" VLANs configurés: {len(vlans_data['vlans'])} VLANs")
        
        # 2. Configuration SSH
        print("\n Étape 2/3: Configuration SSH...")
        ssh_commands = generate_ssh_commands(vlans_data)
        output = connection.send_config_set(ssh_commands, cmd_verify=False)
        print(" SSH activé (Version 2)")
        
        # 3. Configuration Interfaces
        print("\n Étape 3/3: Configuration des interfaces SVI...")
        interface_commands = generate_interface_commands(vlans_data)
        output = connection.send_config_set(interface_commands)
        print(" Interfaces SVI configurées")
        
        # Sauvegarde
        print("\n Sauvegarde de la configuration...")
        connection.save_config()
        
        # Vérification
        print("\n Vérification finale...")
        uptime = connection.send_command("show version | include uptime")
        vlans = connection.send_command("show vlan brief")
        
        connection.disconnect()
        
        print(f"\n{'='*60}")
        print(f" DÉPLOIEMENT RÉUSSI en {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Uptime: {uptime}")
        print(f"VLANs actifs:\n{vlans}")
        
        return True
        
    except NetmikoTimeoutException:
        print(f" Erreur: Timeout - Vérifiez la connectivité avec {device_info['ip']}")
        return False
    except NetmikoAuthenticationException:
        print(f" Erreur: Échec d'authentification sur {device_info['ip']}")
        return False
    except Exception as e:
        print(f" Erreur inattendue: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Déploiement Flash - Automatisation Cisco",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python deploy_flash.py --device Router-Core-01
  python deploy_flash.py --all
  python deploy_flash.py --device 192.168.1.1 --dry-run
        """
    )
    parser.add_argument("--device", help="Nom ou IP du device à configurer")
    parser.add_argument("--all", action="store_true", help="Déployer sur tous les devices")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans application")
    
    args = parser.parse_args()
    
    if not args.device and not args.all:
        parser.print_help()
        sys.exit(1)
    
    devices, vlans_data = load_variables()
    
    if args.all:
        results = []
        for device in devices:
            success = deploy_configuration(device, vlans_data, args.dry_run)
            results.append((device["name"], success))
        
        print(f"\n{'='*60}")
        print(" RAPPORT DE DÉPLOIEMENT")
        print(f"{'='*60}")
        for name, success in results:
            status = "OK" if success else "ÉCHEC"
            print(f"{status} - {name}")
    
    else:
        device = find_device(devices, args.device)
        if not device:
            print(f" Device '{args.device}' non trouvé dans vars/devices.yml")
            sys.exit(1)
        
        deploy_configuration(device, vlans_data, args.dry_run)


if __name__ == "__main__":
    main()
