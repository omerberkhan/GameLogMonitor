import os
import time
import random
from pathlib import Path
import argparse
from datetime import datetime, timezone

# Sample player names
PLAYER_NAMES = [
    "JediMaster", "SithLord", "SpaceRanger", "CosmicPilot", "StarHunter",
    "GalaxyRover", "AstroNinja", "NebulaKnight", "OrbitWarrior", "VoidWalker",
    "StarDust", "CosmicDrifter", "NovaStriker", "SolarSailor", "MoonRaker",
    "DeepSpaceExplorer", "PlanetHopper", "AsteroidMiner", "CometChaser", "QuasarQuest"
]

# Sample damage types
DAMAGE_TYPES = [
    "Ballistic", "Energy", "Distortion", "Physical", "Heat", "Explosion",
    "Impact", "Collision", "Fall", "Asphyxiation", "Laser", "Missile", "Torpedo",
    "VehicleDestruction", "PlayerDeath", "ShipDestruction"
]

# Sample zones/locations
LOCATIONS = [
    "MISC_Freelancer_MIS_200000056835", "AEGS_Gladius_EA_AI_PIR_Elite_200000056834"
]

# Sample weapons
WEAPONS = [
    "KLWE_LaserRepeater_S3_2984839923407", "BEHR_BallisticCannon_S4_2984839923408",
    "APAR_BallisticGatling_S4_200000056755", "KRIG_BallisticGatling_S3_4353485734857",
    "MRCK_S04_BEHR_Dual_S03_2977299075202", "AMRS_LaserCannon_S3_200000051745"
]

def generate_actor_death_line():
    """Generate a random Actor Death log line in the new format"""
    # Generate timestamp in ISO format
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Generate player IDs
    actor_id = random.randint(200000000000, 209999999999)
    killer_id = random.randint(200000000000, 209999999999)
    
    # Select random data
    actor = random.choice(PLAYER_NAMES)
    killer = random.choice(PLAYER_NAMES)
    # Make sure killer is different from actor
    while killer == actor:
        killer = random.choice(PLAYER_NAMES)
    
    damage_type = random.choice(DAMAGE_TYPES)
    location = random.choice(LOCATIONS)
    weapon = random.choice(WEAPONS)
    
    # Generate random direction
    x = random.uniform(-1.0, 1.0)
    y = random.uniform(-1.0, 1.0)
    z = random.uniform(-1.0, 1.0)
    
    # Format using the new format
    return f"<{timestamp}> [Notice] <Actor Death> CActor::Kill: '{actor}' [{actor_id}] in zone '{location}' killed by '{killer}' [{killer_id}] using '{weapon}' [Class unknown] with damage type '{damage_type}' from direction x: {x:.6f}, y: {y:.6f}, z: {z:.6f} [Team_ActorTech][Actor]"

def generate_old_actor_death_line():
    """Generate a random Actor Death log line in the old format"""
    actor = random.choice(PLAYER_NAMES)
    killer = random.choice(PLAYER_NAMES)
    # Make sure killer is different from actor
    while killer == actor:
        killer = random.choice(PLAYER_NAMES)
    
    damage_type = random.choice(DAMAGE_TYPES)
    location = random.choice(LOCATIONS)
    
    return f"<Actor Death> '{actor}' [12345] in zone '{location}' killed by '{killer}' with damage type '{damage_type}'"

def generate_random_log_line():
    """Generate a random log line (both death and non-death lines)"""
    if random.random() < 0.05:  # 5% chance for old format death line
        return generate_old_actor_death_line()
    elif random.random() < 0.15:  # 15% chance for new format death line
        return generate_actor_death_line()
    else:
        templates = [
            "<System> Loading assets for {location}",
            "<Network> Connection status: {status}",
            "<Physics> Object {object_id} velocity: {velocity}",
            "<Rendering> FPS: {fps}",
            "<Audio> Playing sound effect: {sound}",
            "<Input> Detected keypress: {key}",
            "<Game> Player {player} entered zone {location}"
        ]
        
        template = random.choice(templates)
        
        # Fill in the placeholders with random values
        result = template.format(
            location=random.choice(LOCATIONS),
            status=random.choice(["stable", "unstable", "reconnecting", "optimizing"]),
            object_id=random.randint(10000, 99999),
            velocity=f"{random.randint(0, 100)}.{random.randint(0, 99)}",
            fps=random.randint(30, 120),
            sound=random.choice(["explosion", "laser", "engine", "impact", "alert"]),
            key=random.choice(["W", "A", "S", "D", "Space", "Shift", "Ctrl"]),
            player=random.choice(PLAYER_NAMES)
        )
        
        return result

def generate_test_log(log_path, duration=60, interval=1.0):
    """
    Generate a test log file that simulates a real Game.log
    
    Args:
        log_path: Path to create the log file
        duration: How long to run the generator in seconds
        interval: Time between log entries in seconds
    """
    # Create directory if it doesn't exist
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating test log at: {log_path}")
    print(f"Will run for {duration} seconds, writing a new line every {interval} seconds")
    print("Press Ctrl+C to stop early")
    
    try:
        start_time = time.time()
        end_time = start_time + duration
        
        # Initialize with some initial content
        with open(log_path, 'w') as f:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            f.write(f"<{timestamp}> [Notice] <System> Game initialized\n")
            f.write("<System> Loading game assets\n")
            f.write("<Network> Connecting to server\n")
            
            # Add a sample death line in new format
            f.write(generate_actor_death_line() + "\n")
        
        # Add lines at the specified interval
        while time.time() < end_time:
            with open(log_path, 'a') as f:
                f.write(f"{generate_random_log_line()}\n")
            
            # Occasionally add a burst of lines
            if random.random() < 0.1:  # 10% chance for a burst
                burst_count = random.randint(2, 5)
                for _ in range(burst_count):
                    with open(log_path, 'a') as f:
                        f.write(f"{generate_random_log_line()}\n")
            
            time.sleep(interval)
            
        print(f"\nFinished generating test log at: {log_path}")
        
    except KeyboardInterrupt:
        print("\nTest log generation stopped by user")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a test Game.log file with random entries")
    parser.add_argument("--path", "-p", type=str, default="Game.log", 
                        help="Path where the test log file should be created")
    parser.add_argument("--duration", "-d", type=int, default=60,
                        help="Duration in seconds to run the generator")
    parser.add_argument("--interval", "-i", type=float, default=1.0,
                        help="Interval in seconds between log entries")
    
    args = parser.parse_args()
    
    generate_test_log(args.path, args.duration, args.interval) 