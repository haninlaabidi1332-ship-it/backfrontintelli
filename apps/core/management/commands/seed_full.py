"""
Management command: seed_full

Clears ALL non-user data and re-seeds IntelliOLT with data
matching the SOTETEL Tunisia EVE-NG architecture:

  IP PLAN
  ───────────────────────────────────────────────────────────────
  HQ management VLAN   192.168.100.0/24
    OLT-HQ-01          192.168.100.10
    NET-TRANSPORT-HQ   192.168.100.1  (WAN: 203.0.113.2)
    DL3SW01/02-HQ      192.168.100.2/3
    CL3SW01/02-HQ      192.168.100.4/5

  Sfax branch          172.17.10.0/30  (IPsec tunnel)
    Branch management  172.17.10.128/26
    OLT-SFAX-01        172.17.10.130
    CL3SW01-BRSFX      172.17.10.131

  El Kef branch        172.17.20.0/30  (IPsec tunnel)
    Branch management  172.17.20.128/26
    OLT-ELKEF-01       172.17.20.130
    CL3SW01-BRKEF      172.17.20.131

  Nabeul branch        172.17.30.0/30  (IPsec tunnel)
    Branch management  172.17.30.128/26
    OLT-NABEUL-01      172.17.30.130
    CL3SW01-BRNBL      172.17.30.131

  ISP-WAN
    WAN-INET-T         203.0.113.1
    WAN-MPLS-T         172.16.30.1
"""

import random
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction


class Command(BaseCommand):
    help = "Clear all data and seed IntelliOLT with SOTETEL EVE-NG architecture"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Clearing existing data (users preserved)...")
        self._clear_data()
        self.stdout.write("🚀 Seeding SOTETEL IntelliOLT data...\n")
        with transaction.atomic():
            self._seed_vendors()
            self._seed_gouvernorats()
            self._seed_sites()
            self._seed_racks()
            self._seed_device_types()
            self._seed_olts()
            self._seed_boards_and_interfaces()
            self._seed_gpon_ports()
            self._seed_customers()
            self._seed_onts()
            self._seed_hardware()
            self._seed_splitters()
            self._seed_config_backups()
            self._seed_equipment_history()
            self._seed_network_devices()
            self._seed_topology()
            self._seed_snmp()
            self._seed_bfd()
            self._seed_ml_models()
            self._seed_anomalies()
            self._seed_alerts()
            self._seed_kpis()
            self._seed_ssh_metrics()
            self._seed_network_traffic()
            self._seed_reports()
        self.stdout.write(self.style.SUCCESS("\n✅ SOTETEL seed complete!"))

    # ──────────────────────────────────────────────────────────────────────────
    # 0. Clear
    # ──────────────────────────────────────────────────────────────────────────
    def _clear_data(self):
        from apps.analytics.models import (
            NetworkTraffic, SSHMetricsSnapshot, TopologyLink, NetworkDevice,
            KPIHistory, Report, DashboardWidget,
        )
        from apps.alerting.models import NotificationHistory, Alert, AlertRule, NotificationChannel
        from apps.ai_engine.models import InferenceLog, AnomalyDetection, Prediction, TrainingJob, MLModel
        from apps.bfd_monitor.models import (
            BFDActiveAlert, BFDStateHistory, BFDPollingSchedule, BFDSession, BFDThresholdRule,
        )
        from apps.snmp_collector.models import (
            SnmpAlert, MetricHistory, PollJob, SnmpErrorLog,
            ProfileOID, DeviceProfile, PollingProfile, SnmpThresholdRule, SnmpOID,
        )
        from apps.eve_ng.models import EveNgLabExecution, EveNgDevice, EveNgLab
        from apps.equipements.models import (
            OpticalPath, SplitterPort, Splitter,
            ONT, GponPort, FibreLink, FiberCore, FiberCable,
            IPAddress, NetworkInterface, Board,
            ConfigurationBackup, EquipmentHistory, PowerSupply, FanModule,
            VLAN, OLT, Rack, DeviceType, Customer,
            Site, Delegation, Gouvernorat, Vendor,
        )
        NetworkTraffic.objects.all().delete()
        SSHMetricsSnapshot.objects.all().delete()
        TopologyLink.objects.all().delete()
        NetworkDevice.objects.all().delete()
        KPIHistory.objects.all().delete()
        Report.objects.all().delete()
        DashboardWidget.objects.all().delete()
        NotificationHistory.objects.all().delete()
        Alert.objects.all().delete()
        AlertRule.objects.all().delete()
        NotificationChannel.objects.all().delete()
        InferenceLog.objects.all().delete()
        AnomalyDetection.objects.all().delete()
        Prediction.objects.all().delete()
        TrainingJob.objects.all().delete()
        MLModel.objects.all().delete()
        BFDActiveAlert.objects.all().delete()
        BFDStateHistory.objects.all().delete()
        BFDPollingSchedule.objects.all().delete()
        BFDSession.objects.all().delete()
        BFDThresholdRule.objects.all().delete()
        SnmpAlert.objects.all().delete()
        MetricHistory.objects.all().delete()
        PollJob.objects.all().delete()
        SnmpErrorLog.objects.all().delete()
        ProfileOID.objects.all().delete()
        DeviceProfile.objects.all().delete()
        PollingProfile.objects.all().delete()
        SnmpThresholdRule.objects.all().delete()
        SnmpOID.objects.all().delete()
        EveNgLabExecution.objects.all().delete()
        EveNgDevice.objects.all().delete()
        EveNgLab.objects.all().delete()
        OpticalPath.objects.all().delete()
        SplitterPort.objects.all().delete()
        Splitter.objects.all().delete()
        ONT.all_objects.all().delete()
        GponPort.all_objects.all().delete()
        FibreLink.all_objects.all().delete()
        FiberCore.objects.all().delete()
        FiberCable.objects.all().delete()
        IPAddress.objects.all().delete()
        NetworkInterface.objects.all().delete()
        Board.objects.all().delete()
        ConfigurationBackup.objects.all().delete()
        EquipmentHistory.objects.all().delete()
        PowerSupply.objects.all().delete()
        FanModule.objects.all().delete()
        VLAN.objects.all().delete()
        OLT.all_objects.all().delete()
        Rack.objects.all().delete()
        DeviceType.objects.all().delete()
        Customer.objects.all().delete()
        Site.objects.all().delete()
        Delegation.objects.all().delete()
        Gouvernorat.objects.all().delete()
        Vendor.objects.all().delete()
        self.stdout.write("  ✓ All data cleared")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Vendors
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_vendors(self):
        from apps.equipements.models import Vendor
        for d in [
            {"name": "Huawei", "code": "HW",  "website": "https://www.huawei.com",
             "support_email": "support@huawei.com", "support_phone": "+86-755-28780808"},
            {"name": "Nokia",  "code": "NOK", "website": "https://www.nokia.com",
             "support_email": "support@nokia.com",  "support_phone": "+358-10-22-88000"},
        ]:
            Vendor.objects.get_or_create(code=d["code"], defaults=d)
        self.stdout.write("  ✓ Vendors (Huawei, Nokia)")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Gouvernorats & Délégations
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_gouvernorats(self):
        from apps.equipements.models import Gouvernorat, Delegation
        govs = [
            ("TN", "Tunis",   [("Tunis Médina", "01"), ("La Marsa", "02"), ("Le Bardo", "03")]),
            ("SF", "Sfax",    [("Sfax Ville",    "01"), ("Sfax Sud", "02"), ("Sakiet Eddaïer", "03")]),
            ("KF", "El Kef",  [("Le Kef Ouest",  "01"), ("Le Kef Est",  "02")]),
            ("NB", "Nabeul",  [("Nabeul",        "01"), ("Hammamet",    "02"), ("Kélibia", "03")]),
        ]
        for code, nom, delegations in govs:
            g, _ = Gouvernorat.objects.get_or_create(code=code, defaults={"nom": nom})
            for del_nom, del_code in delegations:
                Delegation.objects.get_or_create(
                    gouvernorat=g, code=del_code, defaults={"nom": del_nom},
                )
        self.stdout.write("  ✓ Gouvernorats & Délégations")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Sites
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_sites(self):
        from apps.equipements.models import Site, Gouvernorat
        sites_data = [
            ("SITE-HQ-TUN",  "Tunis HQ — POP Central",   "TN", 36.8190, 10.1658, "Tunis",  "1000"),
            ("SITE-SFX-01",  "Branch Sfax",               "SF", 34.7406, 10.7603, "Sfax",   "3000"),
            ("SITE-KEF-01",  "Branch El Kef",             "KF", 36.1677,  8.7048, "El Kef", "7100"),
            ("SITE-NAB-01",  "Branch Nabeul",             "NB", 36.4563, 10.7356, "Nabeul", "8000"),
        ]
        for code, name, gov_code, lat, lon, city, cp in sites_data:
            gov = Gouvernorat.objects.get(code=gov_code)
            Site.objects.get_or_create(
                code=code,
                defaults={
                    "name": name, "city": city, "gouvernorat": gov,
                    "latitude": lat, "longitude": lon, "code_postal": cp,
                    "address": f"Zone Industrielle Télécom, {city}, Tunisie",
                    "contact_name": "Équipe NOC SOTETEL",
                    "contact_phone": "+216 71 000 000",
                },
            )
        self.stdout.write("  ✓ Sites")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Racks
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_racks(self):
        from apps.equipements.models import Site, Rack
        rack_counts = {"SITE-HQ-TUN": 3, "SITE-SFX-01": 2, "SITE-KEF-01": 1, "SITE-NAB-01": 1}
        for site in Site.objects.all():
            for i in range(1, rack_counts.get(site.code, 1) + 1):
                Rack.objects.get_or_create(
                    code=f"{site.code}-RACK-{i:02d}",
                    defaults={
                        "site": site, "name": f"Baie {i:02d}", "total_units": 42,
                        "room": "Salle Technique A" if i == 1 else "Salle Extension B",
                        "row": f"R{i}", "position": f"{i}",
                    },
                )
        self.stdout.write("  ✓ Racks")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Device Types
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_device_types(self):
        from apps.equipements.models import Vendor, DeviceType
        hw  = Vendor.objects.get(code="HW")
        nok = Vendor.objects.get(code="NOK")
        for vendor, model, cls, u_h, pw, part in [
            (hw,  "MA5800-X17",   "olt",  17, 600, "02311GCH"),
            (hw,  "MA5800-X7",    "olt",   7, 400, "02311GCJ"),
            (hw,  "HG8245H",      "ont",   1,  12, "02353EBP"),
            (hw,  "HG8310M",      "ont",   1,   8, "02353HPV"),
            (nok, "7360 ISAM FX", "olt",   7, 350, "3FE68614AA"),
            (nok, "G-010S-P",     "ont",   1,   6, "3FE46542AB"),
        ]:
            DeviceType.objects.get_or_create(
                vendor=vendor, model=model,
                defaults={
                    "device_class": cls, "u_height": u_h,
                    "power_consumption_w": pw, "part_number": part,
                    "description": f"{vendor.name} {model} — équipement FTTH SOTETEL",
                },
            )
        self.stdout.write("  ✓ Device Types")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. OLTs — Realistic IPs matching the EVE-NG IP plan
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_olts(self):
        from apps.equipements.models import Vendor, Site, DeviceType, OLT, Rack, Gouvernorat
        from apps.users.models import User
        hw  = Vendor.objects.get(code="HW")
        nok = Vendor.objects.get(code="NOK")
        admin = User.objects.filter(is_superuser=True).first()
        now  = timezone.now()

        olts_data = [
            # hostname,           ip,               mgmt_ip,          vendor, model,
            # status,  site_code,    pon, onts, serial,             lat,     lon,
            # purchase_date, warranty_end, end_of_support, maintenance_contract, description
            (
                "OLT-HQ-01",
                "192.168.100.10", "192.168.100.10", hw, "MA5800-X7",
                "active", "SITE-HQ-TUN", 4, 64,
                "HW-MA5800-HQ-20210815",
                36.8190, 10.1658,
                date(2021, 8, 15), date(2024, 8, 14), date(2028, 8, 14),
                "SOTETEL-MAIN-2021",
                "OLT agrégateur HQ Tunis — gestion, supervision et ONTs tests NOC.",
            ),
            (
                "OLT-SFAX-01",
                "172.17.10.130", "172.17.10.130", hw, "MA5800-X17",
                "active", "SITE-SFX-01", 16, 64,
                "HW-MA5800-SFX-20220305",
                34.7406, 10.7603,
                date(2022, 3, 5), date(2025, 3, 4), date(2029, 3, 4),
                "SOTETEL-SFX-2022",
                "OLT principal Branch Sfax — dessert 12 ports actifs, ~450 abonnés FTTH résidentiel et entreprise.",
            ),
            (
                "OLT-ELKEF-01",
                "172.17.20.130", "172.17.20.130", nok, "7360 ISAM FX",
                "active", "SITE-KEF-01", 8, 64,
                "NOK-7360-KEF-20230110",
                36.1677, 8.7048,
                date(2023, 1, 10), date(2026, 1, 9), date(2030, 1, 9),
                "SOTETEL-KEF-2023",
                "OLT Branch El Kef — zone rurale, 8 ports GPON, ~160 abonnés. Lien WAN via MPLS.",
            ),
            (
                "OLT-NABEUL-01",
                "172.17.30.130", "172.17.30.130", hw, "MA5800-X7",
                "active", "SITE-NAB-01", 8, 64,
                "HW-MA5800-NAB-20220920",
                36.4563, 10.7356,
                date(2022, 9, 20), date(2025, 9, 19), date(2029, 9, 19),
                "SOTETEL-NAB-2022",
                "OLT Branch Nabeul-Hammamet — zone côtière, 8 ports GPON, ~280 abonnés mixte résidentiel/hôtellerie.",
            ),
        ]
        for (hostname, ip, mgmt_ip, vendor, model, status, site_code, max_pon, max_ont,
             serial, lat, lon, pur_date, war_end, eos, contract, desc) in olts_data:
            site = Site.objects.get(code=site_code)
            dt   = DeviceType.objects.get(vendor=vendor, model=model)
            rack = Rack.objects.filter(site=site).order_by("code").first()
            gov  = site.gouvernorat
            OLT.objects.get_or_create(
                hostname=hostname,
                defaults={
                    "ip_address":           ip,
                    "management_ip":        mgmt_ip,
                    "vendor":               vendor,
                    "device_type":          dt,
                    "site":                 site,
                    "rack":                 rack,
                    "rack_unit":            2,
                    "status":               status,
                    "snmp_community":       "sotetel_snmp_ro",
                    "snmp_version":         "2c",
                    "snmp_port":            161,
                    "max_pon_ports":        max_pon,
                    "max_onts_per_port":    max_ont,
                    "firmware_version":     "V800R021C10SPC300" if vendor.code == "HW" else "FP3.R6",
                    "hardware_version":     "VER.B"             if vendor.code == "HW" else "Rev.03",
                    "serial_number":        serial,
                    "asset_tag":            f"AST-{hostname}",
                    "purchase_date":        pur_date,
                    "warranty_end":         war_end,
                    "end_of_support":       eos,
                    "maintenance_contract": contract,
                    "description":          desc,
                    "city":                 site.city,
                    "region":               gov.nom if gov else "",
                    "gouvernorat":          gov,
                    "latitude":             lat,
                    "longitude":            lon,
                    "uptime_seconds":       random.randint(2_592_000, 15_552_000),
                    "last_polled_at":       now - timedelta(seconds=random.randint(30, 90)),
                    "created_by":           admin,
                },
            )
        self.stdout.write("  ✓ OLTs (IPs: 192.168.100.10 / 172.17.10.130 / 172.17.20.130 / 172.17.30.130)")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Boards & NetworkInterfaces
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_boards_and_interfaces(self):
        from apps.equipements.models import OLT, Board, NetworkInterface

        cfg_map = {
            "OLT-HQ-01":     {"uplink_mbps": 10000, "gpon_ports":  4},
            "OLT-SFAX-01":   {"uplink_mbps": 10000, "gpon_ports": 16},
            "OLT-ELKEF-01":  {"uplink_mbps":  1000, "gpon_ports":  8},
            "OLT-NABEUL-01": {"uplink_mbps": 10000, "gpon_ports":  8},
        }
        # Stable MAC prefix per OLT
        mac_prefix = {
            "OLT-HQ-01":     "2C:AB:01",
            "OLT-SFAX-01":   "2C:AB:02",
            "OLT-ELKEF-01":  "2C:AB:03",
            "OLT-NABEUL-01": "2C:AB:04",
        }
        fw_map = {
            "OLT-HQ-01":     "V800R021C10SPC300",
            "OLT-SFAX-01":   "V800R021C10SPC300",
            "OLT-ELKEF-01":  "FP3.R6",
            "OLT-NABEUL-01": "V800R021C10SPC300",
        }
        for olt in OLT.objects.all():
            cfg  = cfg_map.get(olt.hostname, {"uplink_mbps": 10000, "gpon_ports": 8})
            pfx  = mac_prefix.get(olt.hostname, "2C:AB:FF")
            fw   = fw_map.get(olt.hostname, "V800R021C10SPC300")
            is_hw = olt.vendor.code == "HW"

            ctrl, _ = Board.objects.get_or_create(
                olt=olt, slot_number=0,
                defaults={"board_type": "control",
                          "model": "SCUN" if is_hw else "CFC",
                          "status": "active", "firmware_version": fw,
                          "serial_number": f"SN-CTRL-{olt.hostname}"},
            )
            gpon_board, _ = Board.objects.get_or_create(
                olt=olt, slot_number=1,
                defaults={"board_type": "gpon",
                          "model": "GPBD" if is_hw else "FGLT-B",
                          "status": "active", "firmware_version": fw,
                          "serial_number": f"SN-GPON-{olt.hostname}"},
            )
            uplink_board, _ = Board.objects.get_or_create(
                olt=olt, slot_number=2,
                defaults={"board_type": "uplink",
                          "model": "X2CS" if is_hw else "ETLI",
                          "status": "active", "firmware_version": fw,
                          "serial_number": f"SN-UPLK-{olt.hostname}"},
            )

            NetworkInterface.objects.get_or_create(
                olt=olt, name="eth0",
                defaults={
                    "board": ctrl, "interface_type": "ethernet",
                    "admin_status": True, "oper_status": True,
                    "speed_mbps": cfg["uplink_mbps"],
                    "mac_address": f"{pfx}:E0:00:01",
                    "description": "Uplink principal — vers ISP-WAN / routeur de branche",
                    "mtu": 9000,
                },
            )
            NetworkInterface.objects.get_or_create(
                olt=olt, name="eth1",
                defaults={
                    "board": uplink_board, "interface_type": "ethernet",
                    "admin_status": True,
                    "oper_status": olt.hostname != "OLT-ELKEF-01",
                    "speed_mbps": cfg["uplink_mbps"],
                    "mac_address": f"{pfx}:E0:00:02",
                    "description": "Uplink secondaire — redondance active/standby",
                    "mtu": 9000,
                },
            )
            for i in range(1, cfg["gpon_ports"] + 1):
                NetworkInterface.objects.get_or_create(
                    olt=olt, name=f"0/1/{i}",
                    defaults={
                        "board": gpon_board, "interface_type": "gpon",
                        "admin_status": True, "oper_status": True,
                        "speed_mbps": 2488,
                        "mac_address": f"{pfx}:GP:{i:02X}:03",
                        "description": f"Port GPON {i} — jusqu'à 64 ONTs",
                        "mtu": 1518,
                    },
                )
        self.stdout.write("  ✓ Boards & Interfaces")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. GPON Ports
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_gpon_ports(self):
        from apps.equipements.models import OLT, GponPort
        ont_cfg = {
            "OLT-HQ-01":     {"ports":  4, "min": 10, "max": 14},
            "OLT-SFAX-01":   {"ports": 12, "min": 35, "max": 42},
            "OLT-ELKEF-01":  {"ports":  8, "min": 17, "max": 22},
            "OLT-NABEUL-01": {"ports":  8, "min": 32, "max": 37},
        }
        for olt in OLT.objects.all():
            cfg = ont_cfg.get(olt.hostname, {"ports": 8, "min": 20, "max": 40})
            for idx in range(1, cfg["ports"] + 1):
                GponPort.objects.get_or_create(
                    olt=olt, port_index=idx,
                    defaults={
                        "port_name":        f"0/1/{idx}",
                        "enabled":          True,
                        "ont_count":        random.randint(cfg["min"], cfg["max"]),
                        "rx_power_min_dbm": -28.0,
                        "rx_power_max_dbm": -8.0,
                    },
                )
        self.stdout.write("  ✓ GPON Ports")

    # ──────────────────────────────────────────────────────────────────────────
    # 9. Customers
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_customers(self):
        from apps.equipements.models import Customer
        first_names = [
            "Mohamed","Ahmed","Fatma","Sarra","Khaled","Nour","Rim","Yassine",
            "Amine","Hajer","Rami","Imen","Malek","Wafa","Tarek","Salma",
            "Hamza","Donia","Anis","Leila","Walid","Mariam","Bilel","Asma",
            "Karim","Nadia","Hichem","Olfa","Zied","Chiraz",
        ]
        last_names = [
            "Ben Ali","Trabelsi","Chaabane","Mansour","Jebali","Khlifi","Lamine",
            "Chtioui","Bouzid","Hamdani","Gharbi","Ferchichi","Saidi","Arfaoui",
            "Boukadida","Dkhili","Hamdi","Mrad","Tlili","Ghanmi",
        ]
        streets = [
            "Avenue Habib Bourguiba","Rue Ibn Khaldoun","Avenue de la Liberté",
            "Rue de Marseille","Avenue Mohamed V","Rue de Palestine",
            "Rue Tahar Ben Achour","Impasse des Jasmins","Avenue Farhat Hached",
        ]
        city_map = {
            "STEL0001": "Tunis", "STEL0200": "Sfax",
            "STEL0500": "El Kef", "STEL0650": "Nabeul",
        }
        branch_cities = ["Tunis", "Sfax", "El Kef", "Nabeul", "Hammamet"]
        for i in range(1, 701):
            fn   = random.choice(first_names)
            ln   = random.choice(last_names)
            city = random.choice(branch_cities)
            Customer.objects.get_or_create(
                customer_id=f"STEL{i:06d}",
                defaults={
                    "full_name": f"{fn} {ln}",
                    "email":     f"client{i}@sotetel.tn",
                    "phone":     f"+216{random.randint(20000000, 99999999)}",
                    "address":   f"{random.randint(1,200)} {random.choice(streets)}, {city}, Tunisie",
                },
            )
        self.stdout.write("  ✓ Customers (700)")

    # ──────────────────────────────────────────────────────────────────────────
    # 10. ONTs — Branch-specific IPs and coordinates
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_onts(self):
        from apps.equipements.models import OLT, GponPort, Customer, ONT, Vendor
        hw  = Vendor.objects.get(code="HW")
        nok = Vendor.objects.get(code="NOK")
        customers = list(Customer.objects.all())
        now = timezone.now()

        # Mostly online — healthy ISP (90% online, 5% offline, 5% degraded/LOS)
        statuses_normal = ["online"] * 18 + ["offline"] * 1 + ["degraded"] * 1
        # El Kef had a partial outage so slightly more offline
        statuses_elkef  = ["online"] * 15 + ["offline"] * 3 + ["los"] * 1 + ["degraded"] * 1

        # RX power per branch (dBm) — depends on fiber distance
        rx_ranges = {
            "OLT-HQ-01":     (-16.0, -10.0),
            "OLT-SFAX-01":   (-22.0, -13.0),
            "OLT-ELKEF-01":  (-25.0, -16.0),
            "OLT-NABEUL-01": (-21.0, -14.0),
        }
        dist_ranges = {
            "OLT-HQ-01":     (0.2,  3.0),
            "OLT-SFAX-01":   (0.5, 12.0),
            "OLT-ELKEF-01":  (1.0, 20.0),
            "OLT-NABEUL-01": (0.5, 10.0),
        }
        # Subscriber IP pools per branch (CGNAT 100.64.0.0/10 sub-ranges)
        ip_pools = {
            "OLT-HQ-01":     ("100.64",  0,  99),
            "OLT-SFAX-01":   ("100.65",  0, 254),
            "OLT-ELKEF-01":  ("100.66",  0, 254),
            "OLT-NABEUL-01": ("100.67",  0, 254),
        }
        # Geographic center per branch (with small radius scatter)
        geo_centers = {
            "OLT-HQ-01":     (36.8190, 10.1658, 0.03),
            "OLT-SFAX-01":   (34.7406, 10.7603, 0.08),
            "OLT-ELKEF-01":  (36.1677,  8.7048, 0.12),
            "OLT-NABEUL-01": (36.4563, 10.7356, 0.06),
        }
        city_map = {
            "OLT-HQ-01":     "Tunis",
            "OLT-SFAX-01":   "Sfax",
            "OLT-ELKEF-01":  "El Kef",
            "OLT-NABEUL-01": "Nabeul",
        }
        addresses_map = {
            "OLT-HQ-01":     ["Rue de Rome", "Avenue Bourguiba", "Rue de Carthage"],
            "OLT-SFAX-01":   ["Rue de la République", "Avenue Farhat Hached", "Route de Tunis"],
            "OLT-ELKEF-01":  ["Avenue de la Liberté", "Rue Habib Thameur", "Cité Ennasr"],
            "OLT-NABEUL-01": ["Avenue Hammamet", "Route Touristique", "Rue des Roses"],
        }

        ont_idx  = 1
        ont_bulk = []

        for olt in OLT.objects.all():
            ports               = list(GponPort.objects.filter(olt=olt))
            rx_min,   rx_max    = rx_ranges.get(olt.hostname,   (-24.0, -14.0))
            dist_min, dist_max  = dist_ranges.get(olt.hostname, (0.5, 10.0))
            ip_pfx, ip_lo, ip_hi = ip_pools.get(olt.hostname,  ("100.68", 0, 254))
            geo_lat, geo_lon, geo_r = geo_centers.get(olt.hostname, (36.8, 10.1, 0.05))
            city                = city_map.get(olt.hostname, olt.site.city)
            streets             = addresses_map.get(olt.hostname, ["Avenue de la Liberté"])
            statuses            = statuses_elkef if olt.hostname == "OLT-ELKEF-01" else statuses_normal
            is_hw               = olt.vendor.code == "HW"

            for port in ports:
                for n in range(1, port.ont_count + 1):
                    sn      = f"STEL{ont_idx:08d}"
                    mac_hex = f"{ont_idx:012X}"
                    mac     = ":".join(mac_hex[i:i+2] for i in range(0, 12, 2))
                    status  = random.choice(statuses)
                    rx      = round(random.uniform(rx_min, rx_max), 2)
                    tx      = round(random.uniform(-3.0, 2.0), 2)
                    dist    = round(random.uniform(dist_min, dist_max), 2)
                    svc     = random.choice(["residential"] * 8 + ["business"] * 2)
                    cust    = random.choice(customers) if random.random() > 0.04 else None

                    ip_b    = random.randint(ip_lo, ip_hi)
                    ip_c    = random.randint(1, 254)
                    sub_ip  = f"{ip_pfx}.{ip_b}.{ip_c}"

                    lat = round(geo_lat + random.uniform(-geo_r, geo_r), 5)
                    lon = round(geo_lon + random.uniform(-geo_r, geo_r), 5)

                    if is_hw:
                        ont_vendor = hw
                        ont_model  = random.choice(["HG8245H", "HG8310M"])
                        ont_fw     = random.choice(["V3R016C10S100", "V3R017C00S060", "V3R016C10S115"])
                    else:
                        ont_vendor = nok
                        ont_model  = "G-010S-P"
                        ont_fw     = random.choice(["3FE45458AAAA01", "3FE45458AAAB02"])

                    last_seen = (
                        now - timedelta(minutes=random.randint(1, 15))
                        if status == "online"
                        else now - timedelta(hours=random.randint(1, 48))
                    )
                    ont_bulk.append(ONT(
                        serial_number    = sn,
                        mac_address      = mac,
                        ip_address       = sub_ip,
                        olt              = olt,
                        gpon_port        = port,
                        ont_index        = n,
                        rx_power         = rx,
                        tx_power         = tx,
                        distance_km      = dist,
                        attenuation_db   = round(abs(rx) * 0.33, 2),
                        vendor           = ont_vendor,
                        model            = ont_model,
                        firmware_version = ont_fw,
                        status           = status,
                        last_seen_at     = last_seen,
                        customer         = cust,
                        service_type     = svc,
                        city             = city,
                        address          = f"{random.randint(1,200)} {random.choice(streets)}, {city}",
                        latitude         = lat,
                        longitude        = lon,
                    ))
                    ont_idx += 1

                    if len(ont_bulk) >= 300:
                        ONT.objects.bulk_create(ont_bulk, ignore_conflicts=True)
                        ont_bulk = []

        if ont_bulk:
            ONT.objects.bulk_create(ont_bulk, ignore_conflicts=True)

        self.stdout.write(f"  ✓ ONTs ({ONT.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 11. Hardware (PowerSupply + FanModule per OLT)
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_hardware(self):
        from apps.equipements.models import OLT, PowerSupply, FanModule

        # Fan counts and RPM ranges per model
        hw_cfg = {
            "MA5800-X17": {"fans": 4, "rpm_lo": 3200, "rpm_hi": 4400, "pwr": 600},
            "MA5800-X7":  {"fans": 2, "rpm_lo": 2800, "rpm_hi": 3800, "pwr": 400},
            "7360 ISAM FX":{"fans": 2, "rpm_lo": 2600, "rpm_hi": 3600, "pwr": 350},
        }
        for olt in OLT.objects.all():
            cfg = hw_cfg.get(olt.device_type.model, {"fans": 2, "rpm_lo": 2800, "rpm_hi": 3800, "pwr": 400})
            # 2 PSUs per OLT (A=active, B=standby)
            for slot, status in [("PSU-A", "active"), ("PSU-B", "active")]:
                PowerSupply.objects.get_or_create(
                    olt=olt, slot=slot,
                    defaults={"status": status, "power_watts": cfg["pwr"]},
                )
            # Fan modules
            for f in range(1, cfg["fans"] + 1):
                FanModule.objects.get_or_create(
                    olt=olt, name=f"FAN-{f}",
                    defaults={
                        "speed_rpm": random.randint(cfg["rpm_lo"], cfg["rpm_hi"]),
                        "status":    "active",
                    },
                )
        self.stdout.write(f"  ✓ Hardware — PSUs & Fans ({PowerSupply.objects.count()} PSU, {FanModule.objects.count()} fans)")

    # ──────────────────────────────────────────────────────────────────────────
    # 12. Splitters + Optical Paths
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_splitters(self):
        from apps.equipements.models import OLT, Site, Rack, Splitter, SplitterPort, ONT, OpticalPath

        branch_splitters = {
            "SITE-HQ-TUN":  [("SPL-HQ-01", "1:8",  1, 36.8195, 10.1660)],
            "SITE-SFX-01":  [
                ("SPL-SFX-01", "1:16", 1, 34.7410, 10.7608),
                ("SPL-SFX-02", "1:32", 2, 34.7395, 10.7589),
                ("SPL-SFX-03", "1:16", 2, 34.7420, 10.7620),
            ],
            "SITE-KEF-01":  [
                ("SPL-KEF-01", "1:16", 1, 36.1680,  8.7052),
                ("SPL-KEF-02", "1:8",  2, 36.1660,  8.7038),
            ],
            "SITE-NAB-01":  [
                ("SPL-NAB-01", "1:32", 1, 36.4568, 10.7360),
                ("SPL-NAB-02", "1:16", 2, 36.4550, 10.7345),
            ],
        }
        ratio_ports = {"1:8": 8, "1:16": 16, "1:32": 32}
        created_splitters = {}

        for site in Site.objects.all():
            rack = Rack.objects.filter(site=site).first()
            for name, ratio, level, lat, lon in branch_splitters.get(site.code, []):
                spl, _ = Splitter.objects.get_or_create(
                    name=name,
                    defaults={
                        "site": site, "ratio": ratio, "level": level,
                        "latitude": lat, "longitude": lon, "rack": rack,
                    },
                )
                created_splitters[name] = spl

                n_ports = ratio_ports.get(ratio, 16)
                # 1 input port
                SplitterPort.objects.get_or_create(
                    splitter=spl, port_number=1,
                    defaults={"direction": "input", "is_used": True},
                )
                # Output ports (to be wired to ONTs below)
                for p in range(1, n_ports + 1):
                    SplitterPort.objects.get_or_create(
                        splitter=spl, port_number=p + 1,
                        defaults={"direction": "output", "is_used": False},
                    )

        # Wire ONTs to splitters via OpticalPath (first 20 ONTs per branch OLT)
        for olt in OLT.objects.all():
            site_code = olt.site.code
            spls      = [s for name, s in created_splitters.items()
                         if name.startswith(f"SPL-{site_code.split('-')[1]}")]
            if not spls:
                continue
            onts = list(ONT.objects.filter(olt=olt, status="online")[:20])
            for i, ont in enumerate(onts):
                spl          = spls[i % len(spls)]
                fiber_km     = round(ont.distance_km * 0.6, 2) if ont.distance_km else 0.5
                loss          = round(fiber_km * 0.2 + 3.5, 2)
                OpticalPath.objects.get_or_create(
                    olt=olt, splitter=spl, ont=ont,
                    defaults={"fiber_length_km": fiber_km, "total_loss_db": loss, "is_active": True},
                )
                # Mark splitter port as used
                port = SplitterPort.objects.filter(
                    splitter=spl, direction="output", is_used=False
                ).first()
                if port:
                    port.is_used    = True
                    port.connected_ont = ont
                    port.save(update_fields=["is_used", "connected_ont"])

        self.stdout.write(
            f"  ✓ Splitters ({Splitter.objects.count()}) + OpticalPaths ({OpticalPath.objects.count()})"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 13. Configuration Backups (3 per OLT, realistic VRP/Nokia config)
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_config_backups(self):
        from apps.equipements.models import OLT, ConfigurationBackup

        def hw_config(olt):
            return f"""#
sysname {olt.hostname}
#
clock timezone Tunisia add 01:00:00
#
vlan batch 10 20 30 100 130 999
#
interface meth0/0/0
 ip address {olt.ip_address} 255.255.255.192
 shutdown disable
#
interface vlanif100
 description GESTION-OLT
 ip address {olt.ip_address} 255.255.255.192
#
snmp-agent
snmp-agent local-engineid 800007DB03{olt.serial_number[-8:] if olt.serial_number else '00000001'}
snmp-agent community read {olt.snmp_community}
snmp-agent sys-info contact NOC-SOTETEL@sotetel.tn
snmp-agent sys-info location {olt.site.city}-{olt.site.code}
snmp-agent sys-info version v2c
snmp-agent trap enable
#
ntp-service server 192.168.100.1
ntp-service enable
#
gpon
 ont-lineprofile gpon-line-profile-1
  tcont 1 dba-profile-index 1
  gem add 0 eth tcont 1
  gem mapping 0 0 vlan 10
 ont-srvprofile gpon-srvprofile-1
  ont-port eth 4 pots 2
#
interface gpon 0/1
{"".join(f" port {i} ont-auto-find enable{chr(10)}" for i in range(1, olt.max_pon_ports+1))}#
return
"""

        def nok_config(olt):
            return f"""configure system name "{olt.hostname}"
configure system contact "NOC-SOTETEL@sotetel.tn"
configure system location "{olt.site.city}/{olt.site.code}"
#
configure router interface "system"
    address {olt.ip_address}/26
    no shutdown
exit
#
configure snmp community "{olt.snmp_community}" read-only
configure snmp trap-target 192.168.100.1 port 162
#
configure equipment ont-type "G-010S-P" serv-pots 0 serv-ethernet 1
#
configure interface port ont:1/1/1/1/1
    no shutdown
exit
#
configure qos
    scheduling-policy "SOTETEL-DEFAULT"
exit
"""

        now = timezone.now()
        for olt in OLT.objects.all():
            is_hw = olt.vendor.code == "HW"
            for weeks_ago in [3, 2, 1]:
                ts       = now - timedelta(weeks=weeks_ago)
                filename = f"{olt.hostname}_backup_{ts.strftime('%Y%m%d_%H%M')}.cfg"
                cfg_text = hw_config(olt) if is_hw else nok_config(olt)
                if not ConfigurationBackup.objects.filter(olt=olt, filename=filename).exists():
                    ConfigurationBackup(
                        olt=olt, filename=filename, config_text=cfg_text,
                    ).save()
        self.stdout.write(f"  ✓ Config Backups ({ConfigurationBackup.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 14. Equipment History (audit trail)
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_equipment_history(self):
        from apps.equipements.models import OLT, EquipmentHistory
        from apps.users.models import User
        admin = User.objects.filter(is_superuser=True).first()
        now   = timezone.now()

        events = {
            "OLT-HQ-01": [
                ("firmware_version",    "V800R021C10SPC200",   "V800R021C10SPC300", 45),
                ("snmp_community",      "public",              "sotetel_snmp_ro",    90),
                ("status",              "maintenance",         "active",             30),
            ],
            "OLT-SFAX-01": [
                ("firmware_version",    "V800R021C10SPC200",   "V800R021C10SPC300", 45),
                ("max_pon_ports",       "8",                   "16",                180),
                ("status",             "degraded",             "active",             20),
            ],
            "OLT-ELKEF-01": [
                ("firmware_version",    "FP3.R5",              "FP3.R6",             60),
                ("ip_address",          "172.17.20.2",         "172.17.20.130",      120),
                ("status",             "maintenance",          "active",              35),
            ],
            "OLT-NABEUL-01": [
                ("firmware_version",    "V800R021C10SPC200",   "V800R021C10SPC300", 45),
                ("snmp_community",      "public",              "sotetel_snmp_ro",    85),
            ],
        }
        for olt in OLT.objects.all():
            for field, old_val, new_val, days_ago in events.get(olt.hostname, []):
                EquipmentHistory(
                    olt=olt, field_name=field,
                    old_value=old_val, new_value=new_val,
                    changed_by=admin,
                ).save()
        self.stdout.write(f"  ✓ Equipment History ({EquipmentHistory.objects.count()} entries)")

    # ──────────────────────────────────────────────────────────────────────────
    # 15. NetworkDevices — Correct IPs matching EVE-NG IP plan
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_network_devices(self):
        from apps.analytics.models import NetworkDevice
        from apps.equipements.models import Site
        hq  = Site.objects.get(code="SITE-HQ-TUN")
        sfx = Site.objects.get(code="SITE-SFX-01")
        kef = Site.objects.get(code="SITE-KEF-01")
        nbl = Site.objects.get(code="SITE-NAB-01")
        now = timezone.now()

        # name, type, ip, hostname, site
        devices = [
            # ISP-WAN side
            ("WAN-INET-T",           "router", "203.0.113.1",  "WAN-INET-T",           hq),
            ("WAN-MPLS-T",           "router", "172.16.30.1",  "WAN-MPLS-T",           hq),
            # HQ LAN (management VLAN 192.168.100.0/24)
            ("NET-TRANSPORT-HQ",     "router", "192.168.100.1", "NET-TRANSPORT-HQ",    hq),
            ("DL3SW01-HQ",           "switch", "192.168.100.2", "DL3SW01-HQ",          hq),
            ("DL3SW02-HQ",           "switch", "192.168.100.3", "DL3SW02-HQ",          hq),
            ("CL3SW01-HQ",           "switch", "192.168.100.4", "CL3SW01-HQ",          hq),
            ("CL3SW02-HQ",           "switch", "192.168.100.5", "CL3SW02-HQ",          hq),
            # Sfax branch management (172.17.10.128/26)
            ("NET-TRANSPORT-BRSFX",  "router", "172.17.10.2",   "NET-TRANSPORT-BRSFX", sfx),
            ("CL3SW01-BRSFX",        "switch", "172.17.10.131", "CL3SW01-BRSFX",       sfx),
            # El Kef branch management (172.17.20.128/26)
            ("NET-TRANSPORT-BRKEF",  "router", "172.17.20.2",   "NET-TRANSPORT-BRKEF", kef),
            ("CL3SW01-BRKEF",        "switch", "172.17.20.131", "CL3SW01-BRKEF",       kef),
            # Nabeul branch management (172.17.30.128/26)
            ("NET-TRANSPORT-BRNBL",  "router", "172.17.30.2",   "NET-TRANSPORT-BRNBL", nbl),
            ("CL3SW01-BRNBL",        "switch", "172.17.30.131", "CL3SW01-BRNBL",       nbl),
        ]
        for name, dtype, ip, host, site in devices:
            NetworkDevice.objects.get_or_create(
                name=name,
                defaults={
                    "device_type":       dtype,
                    "ip_address":        ip,
                    "hostname":          host,
                    "site":              site,
                    "auth_method":       "snmp",
                    "snmp_community":    "sotetel_snmp_ro",
                    "snmp_port":         161,
                    "ssh_username":      "admin",
                    "ssh_port":          22,
                    "is_active":         True,
                    "is_reachable":      True,
                    "last_connection_at":now - timedelta(seconds=random.randint(30, 120)),
                },
            )
        self.stdout.write(f"  ✓ Network Devices ({NetworkDevice.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 16. Topology Links
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_topology(self):
        from apps.analytics.models import NetworkDevice, TopologyLink

        def dev(name):
            return NetworkDevice.objects.get(name=name)

        links = [
            ("NET-TRANSPORT-HQ",    "Gi0/0",  "WAN-INET-T",           "Gi0/2",  "backbone",     1000),
            ("NET-TRANSPORT-HQ",    "Gi0/1",  "WAN-MPLS-T",           "Gi0/1",  "backbone",     1000),
            ("WAN-INET-T",          "Gi0/0",  "NET-TRANSPORT-BRSFX",  "Gi0/1",  "backbone",     1000),
            ("WAN-INET-T",          "Gi0/1",  "NET-TRANSPORT-BRKEF",  "Gi0/2",  "backbone",     1000),
            ("WAN-MPLS-T",          "Gi0/0",  "NET-TRANSPORT-BRNBL",  "Gi0/3",  "backbone",     1000),
            ("NET-TRANSPORT-HQ",    "Gi0/3",  "DL3SW01-HQ",           "Gi0/0",  "distribution", 10000),
            ("DL3SW01-HQ",          "Gi1/0",  "DL3SW02-HQ",           "Gi1/0",  "internal",     10000),
            ("DL3SW01-HQ",          "Gi0/2",  "CL3SW01-HQ",           "Gi1/3",  "distribution", 10000),
            ("DL3SW02-HQ",          "Gi0/2",  "CL3SW02-HQ",           "Gi1/2",  "distribution", 10000),
            ("NET-TRANSPORT-BRSFX", "Gi0/0",  "CL3SW01-BRSFX",        "Gi0/2",  "access",       1000),
            ("NET-TRANSPORT-BRKEF", "Gi0/0",  "CL3SW01-BRKEF",        "Gi0/1",  "access",       1000),
            ("NET-TRANSPORT-BRNBL", "Gi0/0",  "CL3SW01-BRNBL",        "Gi0/2",  "access",       1000),
        ]
        for src_n, src_if, dst_n, dst_if, ltype, bw in links:
            TopologyLink.objects.get_or_create(
                source_device=dev(src_n), source_interface=src_if,
                destination_device=dev(dst_n), destination_interface=dst_if,
                defaults={
                    "link_type":      ltype,
                    "bandwidth_mbps": float(bw),
                    "is_active":      True,
                    "description":    f"{src_n}:{src_if} ↔ {dst_n}:{dst_if}",
                },
            )
        self.stdout.write(f"  ✓ Topology Links ({TopologyLink.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 17. SNMP — 7 days of hourly data, interface-level metrics, error logs
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_snmp(self):
        from apps.snmp_collector.models import (
            SnmpOID, PollingProfile, DeviceProfile, ProfileOID,
            PollJob, MetricHistory, SnmpThresholdRule, SnmpAlert, SnmpErrorLog,
        )
        from apps.equipements.models import OLT, Vendor, DeviceType, NetworkInterface

        # ── OIDs ────────────────────────────────────────────────────────────
        oids_data = [
            # OLT-level
            ("cpu_usage",           "1.3.6.1.4.1.2011.6.3.4.1.2.1",  "CPU OLT (%)",                 "%",   "gauge"),
            ("memory_usage",        "1.3.6.1.4.1.2011.6.3.4.1.3.1",  "Mémoire OLT (%)",             "%",   "gauge"),
            ("temperature",         "1.3.6.1.4.1.2011.6.3.4.1.4.1",  "Température CPU (°C)",        "°C",  "gauge"),
            ("uptime",              "1.3.6.1.2.1.1.3.0",              "Uptime système (ticks)",      "s",   "timeticks"),
            # GPON port-level
            ("ont_online_count",    "1.3.6.1.4.1.2011.6.8.1.1.1.1",  "ONTs en ligne (par port)",    "",    "gauge"),
            ("ont_total_count",     "1.3.6.1.4.1.2011.6.8.1.1.1.2",  "ONTs total (par port)",       "",    "gauge"),
            ("ont_los_count",       "1.3.6.1.4.1.2011.6.8.1.1.1.5",  "ONTs en LOS (par port)",      "",    "gauge"),
            ("rx_power_avg",        "1.3.6.1.4.1.2011.6.8.1.1.1.9",  "Puissance RX moy. (dBm)",     "dBm", "gauge"),
            ("optical_tx_power",    "1.3.6.1.4.1.2011.6.8.1.1.1.8",  "Puissance TX émise (dBm)",    "dBm", "gauge"),
            ("gpon_downstream_bw",  "1.3.6.1.4.1.2011.6.8.1.1.1.10", "Débit DS GPON (kbps)",        "kbps","gauge"),
            ("gpon_upstream_bw",    "1.3.6.1.4.1.2011.6.8.1.1.1.11", "Débit US GPON (kbps)",        "kbps","gauge"),
            # Interface-level (uplink)
            ("if_in_octets",        "1.3.6.1.2.1.2.2.1.10",          "Octets reçus (uplink)",       "B",   "counter"),
            ("if_out_octets",       "1.3.6.1.2.1.2.2.1.16",          "Octets émis (uplink)",        "B",   "counter"),
            ("if_in_errors",        "1.3.6.1.2.1.2.2.1.14",          "Erreurs RX (uplink)",         "",    "counter"),
            ("if_out_errors",       "1.3.6.1.2.1.2.2.1.20",          "Erreurs TX (uplink)",         "",    "counter"),
        ]
        oids = {}
        for name, oid, desc, unit, dtype in oids_data:
            obj, _ = SnmpOID.objects.get_or_create(
                name=name,
                defaults={"oid": oid, "description": desc, "unit": unit,
                          "data_type": dtype, "is_active": True},
            )
            oids[name] = obj

        # ── Polling profile ─────────────────────────────────────────────────
        profile, _ = PollingProfile.objects.get_or_create(
            name="SOTETEL GPON Standard",
            defaults={
                "timeout_seconds": 3.0, "retries": 2,
                "bulk_max_repetitions": 10, "is_default": True,
                "description": "Profil polling standard OLTs SOTETEL",
            },
        )
        hw = Vendor.objects.get(code="HW")
        dt = DeviceType.objects.filter(vendor=hw, device_class="olt").first()
        if dt:
            dp, _ = DeviceProfile.objects.get_or_create(
                name="Huawei MA5800 GPON",
                defaults={"vendor": hw, "device_type": dt,
                          "polling_profile": profile, "is_active": True},
            )
            for oid_obj in oids.values():
                ProfileOID.objects.get_or_create(profile=dp, oid=oid_obj)

        # ── Threshold rules ─────────────────────────────────────────────────
        threshold_data = [
            ("CPU Critique",          "cpu_usage",       ">",  85, "critical", "CPU OLT > 85%"),
            ("CPU Avertissement",     "cpu_usage",       ">",  70, "warning",  "CPU OLT > 70%"),
            ("Mémoire Critique",      "memory_usage",    ">",  90, "critical", "Mémoire OLT > 90%"),
            ("Mémoire Avertissement", "memory_usage",    ">",  75, "warning",  "Mémoire OLT > 75%"),
            ("Temp. Critique",        "temperature",     ">",  75, "critical", "Température > 75°C"),
            ("Temp. Avertissement",   "temperature",     ">",  60, "warning",  "Température > 60°C"),
            ("RX Power Faible",       "rx_power_avg",    "<", -27, "critical", "RX < -27 dBm — LOS imminent"),
            ("LOS Détecté",           "ont_los_count",   ">",   5, "warning",  "> 5 ONTs en LOS sur ce port"),
            ("ONT Online Faible",     "ont_online_count","<",  10, "warning",  "< 10 ONTs en ligne sur ce port"),
        ]
        rules = {}
        for name, oid_name, op, thr, sev, msg in threshold_data:
            r, _ = SnmpThresholdRule.objects.get_or_create(
                name=name,
                defaults={"oid": oids[oid_name], "operator": op, "threshold": thr,
                          "severity": sev, "message": msg, "is_active": True, "cooldown_minutes": 5},
            )
            rules[name] = r

        # ── Metric history — 7 days (168h), per-OLT and per-interface ───────
        now = timezone.now()

        olt_profiles = {
            "OLT-HQ-01": {
                "cpu_usage":         ( 8,  22), "memory_usage":    (25,  42),
                "temperature":       (35,  46), "uptime":          (10_800_000, 10_900_000),
                "ont_online_count":  (44,  50), "ont_total_count": (50,  50),
                "ont_los_count":     ( 0,   1), "rx_power_avg":    (-15.0, -10.5),
                "optical_tx_power":  ( 1.5,  3.0),
                "gpon_downstream_bw":(80_000, 200_000),
                "gpon_upstream_bw":  (20_000,  80_000),
                "if_in_octets":      (50_000_000,    200_000_000),
                "if_out_octets":     (30_000_000,    150_000_000),
                "if_in_errors":      (0, 2), "if_out_errors": (0, 1),
            },
            "OLT-SFAX-01": {
                "cpu_usage":         (35,  65), "memory_usage":    (55,  75),
                "temperature":       (43,  58), "uptime":          (7_776_000, 7_876_000),
                "ont_online_count":  (415, 445),"ont_total_count": (450, 450),
                "ont_los_count":     ( 0,   3), "rx_power_avg":    (-21.0, -13.5),
                "optical_tx_power":  ( 1.0,  2.5),
                "gpon_downstream_bw":(600_000, 1_800_000),
                "gpon_upstream_bw":  (200_000,   600_000),
                "if_in_octets":      (500_000_000, 2_000_000_000),
                "if_out_octets":     (400_000_000, 1_800_000_000),
                "if_in_errors":      (0, 15), "if_out_errors": (0, 8),
            },
            "OLT-ELKEF-01": {
                "cpu_usage":         (15,  30), "memory_usage":    (35,  52),
                "temperature":       (38,  49), "uptime":          (5_184_000, 5_284_000),
                "ont_online_count":  (148, 158),"ont_total_count": (160, 160),
                "ont_los_count":     ( 0,   4), "rx_power_avg":    (-24.5, -17.0),
                "optical_tx_power":  ( 0.5,  2.0),
                "gpon_downstream_bw":(100_000,  450_000),
                "gpon_upstream_bw":  (30_000,   150_000),
                "if_in_octets":      (100_000_000,   500_000_000),
                "if_out_octets":     ( 80_000_000,   400_000_000),
                "if_in_errors":      (0, 5), "if_out_errors": (0, 3),
            },
            "OLT-NABEUL-01": {
                "cpu_usage":         (22,  45), "memory_usage":    (45,  62),
                "temperature":       (40,  53), "uptime":          (8_640_000, 8_740_000),
                "ont_online_count":  (265, 277),"ont_total_count": (280, 280),
                "ont_los_count":     ( 0,   2), "rx_power_avg":    (-22.0, -15.0),
                "optical_tx_power":  ( 1.0,  2.8),
                "gpon_downstream_bw":(250_000,  800_000),
                "gpon_upstream_bw":  (80_000,   280_000),
                "if_in_octets":      (200_000_000,   900_000_000),
                "if_out_octets":     (150_000_000,   750_000_000),
                "if_in_errors":      (0, 8), "if_out_errors": (0, 4),
            },
        }

        metric_bulk = []
        poll_jobs   = []

        for olt in OLT.objects.all():
            mp   = olt_profiles.get(olt.hostname, olt_profiles["OLT-ELKEF-01"])
            eth0 = NetworkInterface.objects.filter(olt=olt, name="eth0").first()

            for h in range(168):          # 7 days of hourly data
                ts  = now - timedelta(hours=h)
                hod = ts.hour             # hour of day
                # Load factor: peak 18-23h, trough 02-06h
                if 18 <= hod <= 23:
                    lf = random.uniform(1.25, 1.45)
                elif 2 <= hod <= 6:
                    lf = random.uniform(0.55, 0.75)
                else:
                    lf = random.uniform(0.90, 1.10)

                # Simulate El Kef partial outage between h=17 and h=18 (18h ago)
                elkef_outage = (olt.hostname == "OLT-ELKEF-01" and 17 <= h <= 18)

                started = ts - timedelta(seconds=random.randint(2, 8))
                poll_jobs.append(PollJob(
                    olt=olt, profile=profile, state="success",
                    started_at=started,
                    finished_at=started + timedelta(seconds=random.randint(2, 6)),
                    metrics_collected=len(oids), metrics_failed=0,
                ))

                for oid_name, oid_obj in oids.items():
                    lo, hi = mp[oid_name]
                    if oid_name in ("if_in_octets", "if_out_octets",
                                    "gpon_downstream_bw", "gpon_upstream_bw"):
                        val = random.uniform(lo, min(hi * lf, hi * 1.5))
                    elif oid_name == "cpu_usage":
                        val = random.uniform(lo, min(hi * lf, 98))
                    elif oid_name == "ont_online_count" and elkef_outage:
                        val = random.uniform(80, 110)   # mass disconnect during outage
                    elif oid_name == "ont_los_count" and elkef_outage:
                        val = random.uniform(40, 60)    # many LOS during outage
                    else:
                        val = random.uniform(lo, hi)

                    # OID-to-interface mapping for uplink metrics
                    iface = eth0 if oid_name in ("if_in_octets", "if_out_octets",
                                                  "if_in_errors", "if_out_errors") else None

                    metric_bulk.append(MetricHistory(
                        olt=olt, oid=oid_obj,
                        interface=iface,
                        raw_value=str(round(val, 3)),
                        numeric_value=round(val, 3),
                        timestamp=ts,
                    ))

                if len(metric_bulk) >= 1000:
                    MetricHistory.objects.bulk_create(metric_bulk)
                    metric_bulk = []

        if metric_bulk:
            MetricHistory.objects.bulk_create(metric_bulk)
        if poll_jobs:
            PollJob.objects.bulk_create(poll_jobs)

        # ── SNMP Alerts ─────────────────────────────────────────────────────
        olt_sfax = OLT.objects.get(hostname="OLT-SFAX-01")
        olt_kef  = OLT.objects.get(hostname="OLT-ELKEF-01")
        SnmpAlert.objects.create(
            rule=rules["RX Power Faible"], olt=olt_kef,
            value=-28.1,
            message="RX -28.1 dBm port 0/1/6 El Kef — LOS corrigé après remplacement connecteur",
            severity="critical", status="acknowledged",
        )
        SnmpAlert.objects.create(
            rule=rules["LOS Détecté"], olt=olt_kef,
            value=47,
            message="47 ONTs en LOS port 0/1/6 El Kef — coupure secteur rue Ibn Khaldoun",
            severity="warning", status="resolved",
        )
        SnmpAlert.objects.create(
            rule=rules["CPU Avertissement"], olt=olt_sfax,
            value=72.4,
            message="CPU 72.4% OLT-SFAX-01 — pic soirée, résolu automatiquement",
            severity="warning", status="resolved",
        )
        SnmpAlert.objects.create(
            rule=rules["Temp. Avertissement"],
            olt=OLT.objects.get(hostname="OLT-NABEUL-01"),
            value=62.3,
            message="Température 62.3°C OLT-NABEUL-01 — vérifier climatisation baie",
            severity="warning", status="active",
        )

        # ── SnmpErrorLog — realistic timeouts/errors ─────────────────────────
        for olt in OLT.objects.all():
            SnmpErrorLog.objects.create(
                olt=olt, oid=oids["cpu_usage"],
                error_type="timeout",
                error_message=f"SNMP timeout after 3s on {olt.ip_address}:161 — retried 2 times",
                occurred_at=now - timedelta(hours=random.randint(2, 48)),
                resolved=True,
            )
        SnmpErrorLog.objects.create(
            olt=OLT.objects.get(hostname="OLT-ELKEF-01"),
            oid=oids["rx_power_avg"],
            error_type="no_such_name",
            error_message="OID 1.3.6.1.4.1.2011.6.8.1.1.1.9 not found — port 0/1/7 not provisioned",
            occurred_at=now - timedelta(hours=20),
            resolved=True,
        )

        self.stdout.write(
            f"  ✓ SNMP ({MetricHistory.objects.count()} métriques, "
            f"{PollJob.objects.count()} poll jobs, "
            f"{SnmpErrorLog.objects.count()} error logs)"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 18. BFD — 3 sessions, 30-day history, El Kef simulated outage
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_bfd(self):
        from apps.equipements.models import OLT, NetworkInterface, FibreLink, FiberCable
        from apps.bfd_monitor.models import (
            BFDSession, BFDStateHistory, BFDPollingSchedule, BFDThresholdRule,
        )

        for name, metric, op, thr, sev, msg, cd in [
            ("BFD Taux Perte Critique", "loss_rate",  ">", 3.0, "critical", "Taux perte BFD > 3%",        5),
            ("BFD Session DOWN",        "state_down", "=", 0,   "critical", "Session BFD DOWN",            1),
            ("BFD Flapping",            "flap_rate",  ">", 5,   "warning",  "Session BFD instable",       10),
            ("BFD Detect Time Élevé",   "detect_time",">", 400, "warning",  "Temps détection BFD > 400ms",  5),
        ]:
            BFDThresholdRule.objects.get_or_create(
                name=name,
                defaults={"metric": metric, "operator": op, "threshold": thr,
                          "severity": sev, "message": msg,
                          "is_active": True, "cooldown_minutes": cd},
            )

        olt_hq = OLT.objects.get(hostname="OLT-HQ-01")
        now    = timezone.now()

        sessions_cfg = [
            # sess,              olt_b_name,       peer_ip,       local_ip,       disc,   up_d,  km,    bw
            ("BFD-HQ-SFAX",   "OLT-SFAX-01",   "172.17.10.130","172.17.10.2",  100001, 45, 271.0, 10000),
            ("BFD-HQ-ELKEF",  "OLT-ELKEF-01",  "172.17.20.130","172.17.20.2",  100003, 18, 175.0,  1000),
            ("BFD-HQ-NABEUL", "OLT-NABEUL-01", "172.17.30.130","172.17.30.2",  100005, 62,  60.0, 10000),
        ]

        for sess_name, olt_b_name, peer_ip, local_ip, disc, uptime_d, km, bw in sessions_cfg:
            olt_b   = OLT.objects.get(hostname=olt_b_name)
            iface_a = NetworkInterface.objects.filter(olt=olt_hq, name="eth0").first()
            iface_b = NetworkInterface.objects.filter(olt=olt_b,  name="eth0").first()
            if not iface_a or not iface_b:
                continue

            cable, _ = FiberCable.objects.get_or_create(
                name=f"CABLE-HQ-{olt_b_name}",
                defaults={"fiber_count": 48, "length_km": km, "cable_type": "armored"},
            )
            link_name = sess_name.replace("BFD-", "LINK-")
            link, _ = FibreLink.objects.get_or_create(
                name=link_name,
                defaults={
                    "interface_a":    iface_a, "interface_b":    iface_b,
                    "link_type":      "backbone",
                    "bandwidth_mbps": float(bw),
                    "utilization_pct":round(random.uniform(15, 55), 1),
                    "attenuation_db": round(km * 0.2, 1),
                    "length_km":      km, "is_active": True,
                },
            )

            if BFDSession.objects.filter(name=sess_name).exists():
                continue

            pkts_sent = random.randint(20_000_000, 80_000_000)
            pkts_lost = random.randint(0, 50)
            pkts_recv = pkts_sent - pkts_lost
            loss_pct  = round(pkts_lost / pkts_sent * 100, 5)

            # El Kef had 1 confirmed down event 18 days ago
            is_elkef  = (sess_name == "BFD-HQ-ELKEF")
            down_cnt  = 1 if is_elkef else 0
            flap_cnt  = 1 if is_elkef else random.randint(0, 2)
            up_cnt    = 2 if is_elkef else random.randint(1, 3)

            sess = BFDSession.objects.create(
                name=sess_name,
                description=f"Tunnel IPsec {local_ip} ↔ {peer_ip} — {olt_b_name}",
                link=link, olt=olt_hq,
                interface_a=iface_a, interface_b=iface_b,
                peer_ip=peer_ip, local_ip=local_ip,
                local_discriminator=disc, remote_discriminator=disc + 1,
                session_type="single_hop",
                desired_tx_interval_ms=100, required_rx_interval_ms=100,
                actual_tx_interval_ms=100,  actual_rx_interval_ms=100,
                detection_multiplier=3,
                state="up", diagnostic=0,
                packets_sent=pkts_sent, packets_received=pkts_recv,
                packets_lost=pkts_lost, loss_rate_pct=loss_pct,
                uptime_seconds=uptime_d * 86400 + random.randint(0, 3600),
                up_count=up_cnt, down_count=down_cnt, flap_count=flap_cnt,
                last_up_at=now - timedelta(days=uptime_d),
                last_down_at=now - timedelta(days=18, hours=17) if is_elkef else None,
                is_enabled=True, is_monitored=True,
            )

            # ── BFD State History — 30 days of events ──────────────────────
            if is_elkef:
                # Normal bring-up events (before the outage period)
                for days_ago in [28, 21]:
                    BFDStateHistory.objects.create(
                        session=sess, previous_state="down", new_state="up",
                        diagnostic=0, timestamp=now - timedelta(days=days_ago),
                    )
                # The actual outage: DOWN then UP recovery
                BFDStateHistory.objects.create(
                    session=sess, previous_state="up", new_state="down",
                    diagnostic=1,   # detection expired
                    duration_previous_ms=18 * 86400 * 1000,
                    timestamp=now - timedelta(days=18, hours=1),
                )
                BFDStateHistory.objects.create(
                    session=sess, previous_state="down", new_state="up",
                    diagnostic=0,
                    duration_previous_ms=3600 * 1000,   # 1h down
                    timestamp=now - timedelta(days=18),
                )
            else:
                for days_ago in [27, 20, 14, 7]:
                    BFDStateHistory.objects.create(
                        session=sess, previous_state="down", new_state="up",
                        diagnostic=0, timestamp=now - timedelta(days=days_ago),
                    )

            # ── Polling schedule ─────────────────────────────────────────────
            for poll_olt in [olt_hq, olt_b]:
                BFDPollingSchedule.objects.get_or_create(
                    olt=poll_olt,
                    defaults={
                        "poll_interval_seconds": 30, "is_active": True,
                        "last_polled_at": now - timedelta(seconds=random.randint(5, 30)),
                    },
                )

        self.stdout.write(
            f"  ✓ BFD Sessions ({BFDSession.objects.count()}) — "
            f"{BFDStateHistory.objects.count()} state history events, "
            f"El Kef outage simulated"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 19. ML Models
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_ml_models(self):
        from apps.ai_engine.models import MLModel, TrainingJob
        from apps.users.models import User
        admin = User.objects.filter(is_superuser=True).first()
        now   = timezone.now()

        for name, mtype, ver, status, acc, active, features in [
            ("Isolation Forest v2.1",     "isolation_forest", "2.1", "active",  0.934, True,
             ["cpu_usage","memory_usage","temperature","rx_power_avg","ont_online_count","ont_los_count"]),
            ("Prophet CPU Forecast v1.3", "prophet",          "1.3", "active",  0.957, True,
             ["cpu_usage"]),
            ("LSTM ONT Counter v1.0",     "lstm",             "1.0", "active",  0.891, True,
             ["ont_online_count","rx_power_avg","ont_los_count"]),
            ("Prophet Traffic v1.0",      "prophet",          "1.0", "active",  0.931, False,
             ["if_in_octets","if_out_octets","gpon_downstream_bw"]),
            ("Grok Explainer v3.0",       "grok",             "3.0", "pending", None,  False, []),
        ]:
            ml, created = MLModel.objects.get_or_create(
                name=name,
                defaults={
                    "model_type":     mtype, "version": ver, "status": status,
                    "accuracy_score": acc, "is_active": active, "features": features,
                    "last_trained_at":now - timedelta(days=random.randint(3, 15)) if acc else None,
                    "trained_by":     admin,
                    "description":    f"Modèle {mtype} pour supervision FTTH SOTETEL",
                    "parameters":     {"n_estimators": 150, "contamination": 0.04}
                                      if mtype == "isolation_forest" else {},
                },
            )
            if created and acc:
                TrainingJob.objects.create(
                    model=ml, status="success",
                    finished_at=now - timedelta(days=random.randint(3, 15)),
                    metrics={"accuracy": acc, "f1_score": round(acc - 0.015, 3),
                             "precision": round(acc + 0.005, 3), "recall": round(acc - 0.02, 3)},
                    data_start_date=now - timedelta(days=90),
                    data_end_date=now - timedelta(days=1),
                    samples_count=random.randint(20000, 80000),
                )
        self.stdout.write("  ✓ ML Models & Training Jobs")

    # ──────────────────────────────────────────────────────────────────────────
    # 20. Anomalies
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_anomalies(self):
        from apps.ai_engine.models import AnomalyDetection, MLModel
        from apps.equipements.models import OLT
        ml  = MLModel.objects.filter(is_active=True, model_type="isolation_forest").first()
        now = timezone.now()

        anomalies = [
            # olt,             metric,           actual,  expected, score, sev,       resolved, h
            ("OLT-ELKEF-01",  "rx_power_avg",    -28.1,  -21.0,   0.94, "critical", True,   18,
             "Puissance optique RX chutée à -28.1 dBm port 0/1/6 El Kef — micro-rupture fibre ou défaut connecteur SC/APC."),
            ("OLT-ELKEF-01",  "ont_online_count",  92,   155.0,   0.92, "critical", True,   17,
             "63 ONTs hors ligne OLT El Kef — coupure alimentation secteur rue Ibn Khaldoun. 47 en LOS."),
            ("OLT-ELKEF-01",  "ont_los_count",     47,     1.0,   0.90, "critical", True,   17,
             "47 ONTs en LOS simultanément — corrélé à la coupure alimentation. Rétabli après 1h."),
            ("OLT-SFAX-01",   "cpu_usage",         78.4,  48.0,   0.82, "high",     True,   36,
             "Pic CPU 78.4% OLT Sfax 45 min — tempête ARP ou rafale re-enregistrement ONTs."),
            ("OLT-SFAX-01",   "memory_usage",      82.1,  62.0,   0.77, "high",     True,   35,
             "Mémoire 82% corrélée au pic CPU — processus SNMP en surcharge."),
            ("OLT-NABEUL-01", "temperature",       62.3,  47.0,   0.73, "high",     False,   5,
             "Température CPU 62.3°C Nabeul — vérifier ventilation baie réseau (chaleur estivale)."),
            ("OLT-SFAX-01",   "rx_power_avg",     -24.8, -17.5,   0.69, "medium",   False,   2,
             "Dégradation optique port 0/1/9 Sfax — atténuation accrue, surveiller évolution."),
            ("OLT-SFAX-01",   "gpon_downstream_bw",1_950_000, 1_200_000, 0.67, "medium", True, 48,
             "Pic trafic descendant 1.95 Gbps OLT Sfax — pic soirée exceptionnel (événement sportif)."),
            ("OLT-HQ-01",     "cpu_usage",         28.5,  12.0,   0.62, "low",      True,   72,
             "Légère hausse CPU HQ lors collecte SNMP batch — comportement normal."),
        ]

        for olt_name, metric, actual, expected, score, sev, resolved, h_ago, expl in anomalies:
            olt = OLT.objects.filter(hostname=olt_name).first()
            if not olt:
                continue
            AnomalyDetection.objects.create(
                olt=olt, metric_name=metric,
                actual_value=actual, expected_value=expected,
                anomaly_score=score, severity=sev, explanation=expl,
                resolved=resolved,
                resolved_at=now - timedelta(hours=h_ago - 1) if resolved else None,
                model=ml, detected_at=now - timedelta(hours=h_ago),
            )
        self.stdout.write(f"  ✓ Anomalies ({AnomalyDetection.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 21. Alerts
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_alerts(self):
        from apps.alerting.models import Alert
        from apps.equipements.models import OLT
        now = timezone.now()

        alerts_data = [
            # olt,              sev,        status,         msg,                                                       val,    h
            ("OLT-ELKEF-01",  "critical", "resolved",     "RX -28.1 dBm port 0/1/6 — LOS corrigé El Kef",           -28.1,  18),
            ("OLT-ELKEF-01",  "critical", "resolved",     "92 ONTs hors ligne — panne secteur rue Ibn Khaldoun",      None,   17),
            ("OLT-ELKEF-01",  "critical", "resolved",     "47 ONTs en LOS simultané — coupure alimentation",          47.0,   17),
            ("OLT-SFAX-01",   "major",    "acknowledged", "CPU 78.4% pendant 45 min — pic trafic soirée",             78.4,   36),
            ("OLT-SFAX-01",   "warning",  "resolved",     "Mémoire 82% corrélée au pic CPU [OLT-SFAX-01]",           82.1,   35),
            ("OLT-NABEUL-01", "major",    "active",       "Température 62.3°C — vérifier climatisation Nabeul",       62.3,    5),
            ("OLT-SFAX-01",   "warning",  "active",       "Dégradation optique port 0/1/9 — RX -24.8 dBm",          -24.8,   2),
            ("OLT-ELKEF-01",  "critical", "resolved",     "BFD-HQ-ELKEF DOWN 1h — lien rétabli (panne secteur)",      None,   17),
            ("OLT-HQ-01",     "info",     "resolved",     "Firmware V800R021C10SPC400 disponible [OLT-HQ-01]",        None,   48),
            ("OLT-SFAX-01",   "info",     "resolved",     "Rapport journalier — 441/450 ONTs en ligne (98%)",         None,   24),
            ("OLT-NABEUL-01", "info",     "resolved",     "Nouveau ONT STEL00000281 enregistré port 0/1/8",           None,   12),
            ("OLT-SFAX-01",   "major",    "resolved",     "Pic trafic 1.95 Gbps — dépassement capacité nominale",     None,   48),
        ]
        for olt_name, sev, status, msg, val, h_ago in alerts_data:
            olt = OLT.objects.filter(hostname=olt_name).first()
            Alert.objects.create(
                olt=olt, severity=sev, status=status, message=msg, value=val,
                first_seen=now - timedelta(hours=h_ago),
                last_seen=now - timedelta(hours=max(0, h_ago - 1)),
                cleared_at=now - timedelta(hours=max(0, h_ago - 2)) if status == "resolved" else None,
            )
        self.stdout.write(f"  ✓ Alerts ({Alert.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 22. KPI History
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_kpis(self):
        from apps.analytics.models import KPIHistory
        from apps.equipements.models import OLT, GponPort
        now  = timezone.now()
        olts = list(OLT.objects.all())

        total_onts  = sum(p.ont_count for o in olts for p in GponPort.objects.filter(olt=o))
        total_olts  = len(olts)
        active_olts = OLT.objects.filter(status="active").count()

        kpi_bulk = []

        # Global hourly — last 7 days (168h)
        for h in range(168):
            ts  = (now - timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
            hod = ts.hour
            if 2 <= hod <= 6:
                online_pct = random.uniform(0.958, 0.975)
                cpu        = random.uniform(12, 24)
            elif 18 <= hod <= 23:
                online_pct = random.uniform(0.928, 0.950)
                cpu        = random.uniform(44, 64)
            else:
                online_pct = random.uniform(0.940, 0.960)
                cpu        = random.uniform(25, 48)

            # El Kef outage visible in global KPIs (h=17..18)
            if 17 <= h <= 18:
                online_pct = random.uniform(0.865, 0.885)
                cpu        = random.uniform(30, 42)

            kpi_bulk.append(KPIHistory(
                period="hour", timestamp=ts, olt=None,
                total_olts=total_olts, active_olts=active_olts,
                total_onts=total_onts, online_onts=int(total_onts * online_pct),
                avg_cpu_usage=round(cpu, 1),
                avg_memory_usage=round(random.uniform(48, 68), 1),
                avg_temperature=round(random.uniform(42, 55), 1),
                avg_rx_power=round(random.uniform(-20.5, -14.0), 2),
                snmp_success_rate=round(random.uniform(97.5, 100.0), 1),
                bfd_up_sessions=2 if 17 <= h <= 18 else 3,
                bfd_total_sessions=3,
                anomaly_count=3 if 17 <= h <= 18 else (1 if h <= 5 else 0),
                alert_count=3 if 17 <= h <= 18 else random.randint(0, 2),
            ))

        # Global daily — last 30 days
        for d in range(30):
            ts      = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            weekend = ts.weekday() >= 5
            outage  = (d == 0)
            online_pct = random.uniform(0.885, 0.908) if outage \
                else (random.uniform(0.945, 0.965) if weekend else random.uniform(0.933, 0.958))
            kpi_bulk.append(KPIHistory(
                period="day", timestamp=ts, olt=None,
                total_olts=total_olts, active_olts=active_olts,
                total_onts=total_onts, online_onts=int(total_onts * online_pct),
                avg_cpu_usage=round(random.uniform(28, 52), 1),
                avg_memory_usage=round(random.uniform(50, 67), 1),
                avg_temperature=round(random.uniform(43, 54), 1),
                avg_rx_power=round(random.uniform(-20.0, -14.5), 2),
                snmp_success_rate=round(random.uniform(97.0, 100.0), 1),
                bfd_up_sessions=2 if outage else 3,
                bfd_total_sessions=3,
                anomaly_count=3 if outage else random.randint(0, 3),
                alert_count=4 if outage else random.randint(0, 5),
            ))

        # Per-OLT daily — last 30 days
        olt_profiles = {
            "OLT-HQ-01":     {"total": 50,  "ol_lo": 0.94, "ol_hi": 0.98, "cpu_lo":  8, "cpu_hi": 22},
            "OLT-SFAX-01":   {"total": 450, "ol_lo": 0.92, "ol_hi": 0.97, "cpu_lo": 35, "cpu_hi": 65},
            "OLT-ELKEF-01":  {"total": 160, "ol_lo": 0.88, "ol_hi": 0.96, "cpu_lo": 15, "cpu_hi": 30},
            "OLT-NABEUL-01": {"total": 280, "ol_lo": 0.93, "ol_hi": 0.97, "cpu_lo": 22, "cpu_hi": 45},
        }
        for olt in olts:
            p = olt_profiles.get(olt.hostname, {"total": 100, "ol_lo": 0.90, "ol_hi": 0.96,
                                                 "cpu_lo": 20, "cpu_hi": 50})
            for d in range(30):
                ts     = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
                outage = (olt.hostname == "OLT-ELKEF-01" and d == 0)
                op     = random.uniform(0.55, 0.65) if outage \
                    else random.uniform(p["ol_lo"], p["ol_hi"])
                kpi_bulk.append(KPIHistory(
                    period="day", timestamp=ts, olt=olt,
                    total_olts=1, active_olts=1,
                    total_onts=p["total"], online_onts=int(p["total"] * op),
                    avg_cpu_usage=round(random.uniform(p["cpu_lo"], p["cpu_hi"]), 1),
                    avg_memory_usage=round(random.uniform(35, 70), 1),
                    avg_temperature=round(random.uniform(38, 58), 1),
                    avg_rx_power=round(random.uniform(-22, -13), 2),
                    snmp_success_rate=round(random.uniform(97, 100), 1),
                    bfd_up_sessions=0 if outage else 1,
                    bfd_total_sessions=1,
                    anomaly_count=3 if outage else 0,
                    alert_count=4 if outage else random.randint(0, 1),
                ))

        KPIHistory.objects.bulk_create(kpi_bulk)
        self.stdout.write(f"  ✓ KPI History ({KPIHistory.objects.count()} entrées)")

    # ──────────────────────────────────────────────────────────────────────────
    # 23. SSH Metrics Snapshots (every 2h over 7 days)
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_ssh_metrics(self):
        from apps.analytics.models import NetworkDevice, SSHMetricsSnapshot
        now = timezone.now()

        profiles = {
            "WAN-INET-T":           {"cpu": (5,  20), "mem": (25, 45), "temp": (38, 50)},
            "WAN-MPLS-T":           {"cpu": (4,  18), "mem": (22, 40), "temp": (36, 48)},
            "NET-TRANSPORT-HQ":     {"cpu": (8,  28), "mem": (30, 50), "temp": (40, 52)},
            "DL3SW01-HQ":           {"cpu": (3,  15), "mem": (20, 35), "temp": (35, 45)},
            "DL3SW02-HQ":           {"cpu": (3,  14), "mem": (20, 35), "temp": (35, 45)},
            "CL3SW01-HQ":           {"cpu": (2,  10), "mem": (15, 28), "temp": (32, 42)},
            "CL3SW02-HQ":           {"cpu": (2,  10), "mem": (15, 28), "temp": (32, 42)},
            "NET-TRANSPORT-BRSFX":  {"cpu": (12, 38), "mem": (35, 58), "temp": (42, 56)},
            "CL3SW01-BRSFX":        {"cpu": (5,  18), "mem": (20, 38), "temp": (36, 48)},
            "NET-TRANSPORT-BRKEF":  {"cpu": (8,  25), "mem": (28, 48), "temp": (38, 52)},
            "CL3SW01-BRKEF":        {"cpu": (3,  12), "mem": (15, 30), "temp": (34, 46)},
            "NET-TRANSPORT-BRNBL":  {"cpu": (10, 32), "mem": (32, 55), "temp": (40, 54)},
            "CL3SW01-BRNBL":        {"cpu": (4,  16), "mem": (18, 35), "temp": (35, 47)},
        }
        ssh_bulk = []
        for device in NetworkDevice.objects.filter(is_active=True):
            prof = profiles.get(device.name, {"cpu": (5, 30), "mem": (20, 50), "temp": (35, 55)})
            for h in range(0, 168, 2):       # every 2h for 7 days
                ts      = now - timedelta(hours=h)
                hod     = ts.hour
                is_peak = 18 <= hod <= 23
                cpu_hi  = prof["cpu"][1] * (1.35 if is_peak else 1.0)
                cpu     = round(random.uniform(prof["cpu"][0], min(cpu_hi, prof["cpu"][1] + 12)), 1)
                mem     = round(random.uniform(prof["mem"][0], prof["mem"][1]), 1)
                temp    = round(random.uniform(prof["temp"][0], prof["temp"][1]), 1)
                ssh_bulk.append(SSHMetricsSnapshot(
                    device=device, timestamp=ts,
                    cpu_usage_pct=cpu, memory_usage_pct=mem,
                    memory_available_mb=int((100 - mem) * 40),
                    temperature_c=temp, temperature_threshold_c=80.0,
                    uptime_seconds=random.randint(1_000_000, 10_000_000),
                    process_count=random.randint(120, 280),
                    active_connections=random.randint(5, 150),
                    is_anomaly=cpu > 85 or mem > 90,
                    collection_duration_ms=random.randint(200, 1800),
                ))
        SSHMetricsSnapshot.objects.bulk_create(ssh_bulk)
        self.stdout.write(f"  ✓ SSH Metrics Snapshots ({SSHMetricsSnapshot.objects.count()})")

    # ──────────────────────────────────────────────────────────────────────────
    # 24. Network Traffic (7 days per backbone fiber link)
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_network_traffic(self):
        from apps.analytics.models import NetworkTraffic
        from apps.equipements.models import FibreLink
        now = timezone.now()

        link_profiles = {
            "LINK-HQ-SFAX":   {"peak": (150, 420), "biz": (80, 250),  "off": (40, 120),  "bw": 10000},
            "LINK-HQ-ELKEF":  {"peak": ( 40, 130), "biz": (25,  80),  "off": (10,  45),  "bw":  1000},
            "LINK-HQ-NABEUL": {"peak": ( 70, 210), "biz": (40, 130),  "off": (20,  75),  "bw": 10000},
        }
        traffic_bulk = []
        for link in FibreLink.objects.filter(is_active=True):
            prof = link_profiles.get(link.name)
            if not prof:
                continue
            for h in range(168):            # 7 days
                ts      = now - timedelta(hours=h)
                hod     = ts.hour
                is_elkef_outage = (link.name == "LINK-HQ-ELKEF" and 17 <= h <= 18)
                if is_elkef_outage:
                    lo, hi = 0, 5           # near-zero traffic during El Kef outage
                elif 18 <= hod <= 23:
                    lo, hi = prof["peak"]
                elif 8 <= hod <= 18:
                    lo, hi = prof["biz"]
                else:
                    lo, hi = prof["off"]

                throughput  = round(random.uniform(lo, hi), 2)
                utilization = round(throughput / prof["bw"] * 100, 2)
                bps         = throughput * 1_000_000 / 8

                traffic_bulk.append(NetworkTraffic(
                    fiber_link=link, timestamp=ts,
                    bytes_in=int(bps * 300 * random.uniform(0.9, 1.1)),
                    bytes_out=int(bps * 300 * random.uniform(0.85, 1.05)),
                    packets_in=int(bps * 300 / 1400),
                    packets_out=int(bps * 300 / 1400 * 0.95),
                    errors_in=random.randint(0, 3),
                    errors_out=random.randint(0, 2),
                    dropped_packets=random.randint(0, 5),
                    throughput_mbps=throughput,
                    utilization_pct=min(utilization, 100.0),
                    is_congested=utilization > 80,
                    is_anomaly=is_elkef_outage,
                ))
        NetworkTraffic.objects.bulk_create(traffic_bulk)
        self.stdout.write(f"  ✓ Network Traffic ({NetworkTraffic.objects.count()} échantillons)")

    # ──────────────────────────────────────────────────────────────────────────
    # 25. Reports
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_reports(self):
        from apps.analytics.models import Report
        from apps.analytics.tasks import generate_report
        from apps.users.models import User
        now   = timezone.now()
        admin = User.objects.filter(is_superuser=True).first()

        report_specs = [
            ("Rapport quotidien SOTETEL — 16 mai 2026",        "daily",   "pdf",  now - timedelta(days=1),  now),
            ("Rapport hebdomadaire — Semaine 20 (2026)",        "weekly",  "pdf",  now - timedelta(days=7),  now),
            ("Rapport mensuel — Avril 2026",                    "monthly", "xlsx", now - timedelta(days=30), now - timedelta(days=1)),
            ("Analyse incident El Kef — panne secteur 16/05",   "custom",  "pdf",  now - timedelta(days=1),  now),
            ("KPI Sfax — Pic trafic soirée (7 derniers jours)", "custom",  "xlsx", now - timedelta(days=7),  now),
            ("Disponibilité OLTs — Q1 2026",                    "custom",  "pdf",  now - timedelta(days=90), now - timedelta(days=60)),
            ("Rapport BFD — Analyse sessions backbone mai 2026","custom",  "pdf",  now - timedelta(days=30), now),
        ]

        generated = 0
        for name, rtype, fmt, dfrom, dto in report_specs:
            report, created = Report.objects.get_or_create(
                name=name,
                defaults={
                    "report_type": rtype, "format": fmt,
                    "date_from":   dfrom, "date_to": dto,
                    "status":      "pending", "generated_by": admin,
                },
            )
            # Always (re)generate the file synchronously so download works
            generate_report(str(report.id))
            report.refresh_from_db()
            if report.status == 'ready':
                generated += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"    ⚠ Rapport '{name[:40]}' : {report.error_message or 'echec'}")
                )

        total = Report.objects.count()
        self.stdout.write(f"  ✓ Reports ({total} total, {generated} fichiers générés)")
