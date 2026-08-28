import unittest
from dataclasses import replace

from games.game_aircraft.logic import (
    CRAFT_SPECS,
    Enemy,
    Explosion,
    PowerUp,
    Projectile,
    advance,
    new_game,
    start,
    toggle_pause,
)


class FixedRng:
    def random(self):
        return 0.0

    def uniform(self, start, _end):
        return start

    def choice(self, values):
        return values[0]


class AircraftLogicTests(unittest.TestCase):
    def test_ready_start_and_pause_transitions(self):
        ready = new_game()
        self.assertEqual(ready.status, "ready")
        self.assertIs(advance(ready, 16).state, ready)

        running = start(ready)
        self.assertEqual(running.status, "running")
        paused = toggle_pause(running)
        self.assertEqual(paused.status, "paused")
        self.assertEqual(toggle_pause(paused).status, "running")

    def test_player_moves_diagonally_at_bounded_speed_and_auto_fires(self):
        state = start(new_game())
        transition = advance(state, 50, (1, -1), FixedRng())
        self.assertGreater(transition.state.player.x, state.player.x)
        self.assertLess(transition.state.player.y, state.player.y)
        self.assertEqual(len(transition.state.projectiles), 1)
        self.assertIn("shot", transition.events)

    def test_destroying_enemy_scores_drops_powerup_and_advances_level(self):
        state = replace(
            start(new_game()),
            kills=9,
            enemies=(Enemy(1, "drone", 180, 100, 0, 0, 1, 1000),),
            projectiles=(Projectile(180, 100, 0, 0, "player"),),
            fire_ms=1000,
        )
        transition = advance(state, 0, rng=FixedRng())
        self.assertEqual(transition.state.score, 100)
        self.assertEqual(transition.state.kills, 10)
        self.assertEqual(transition.state.level, 2)
        self.assertFalse(transition.state.enemies)
        self.assertEqual(transition.state.powerups[0].kind, "rapid")
        self.assertEqual(transition.state.explosions[0].kind, "enemy")
        self.assertIn("destroyed", transition.events)

    def test_aircraft_have_distinct_lives_and_weapon_loadouts(self):
        self.assertEqual(new_game("viper").player.lives, 2)
        self.assertEqual(new_game("guardian").player.lives, 4)
        self.assertGreater(CRAFT_SPECS["viper"].speed, CRAFT_SPECS["falcon"].speed)

        viper = advance(start(new_game("viper")), 0, rng=FixedRng()).state
        guardian = advance(start(new_game("guardian")), 0, rng=FixedRng()).state
        self.assertEqual(len(viper.projectiles), 2)
        self.assertEqual(len(guardian.projectiles), 1)
        self.assertEqual(guardian.projectiles[0].damage, 2)

    def test_unknown_aircraft_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown aircraft"):
            new_game("missing")

    def test_elite_enemy_spawns_with_extra_health_and_faster_fire(self):
        state = replace(
            start(new_game()),
            level=2,
            kills=10,
            spawn_ms=845,
            fire_ms=1000,
        )
        transition = advance(state, 0, rng=FixedRng())
        self.assertEqual(len(transition.state.enemies), 1)
        elite = transition.state.enemies[0]
        self.assertTrue(elite.elite)
        self.assertGreaterEqual(elite.hp, 2)
        self.assertLess(elite.shot_ms, 850)

    def test_boss_arrives_every_five_levels_and_fires_five_way_salvo(self):
        state = replace(
            start(new_game()),
            level=5,
            kills=40,
            next_boss_level=5,
            fire_ms=1000,
        )
        arrival = advance(state, 0, rng=FixedRng())
        boss = arrival.state.enemies[0]
        self.assertEqual(boss.kind, "boss")
        self.assertEqual(arrival.state.next_boss_level, 10)
        self.assertIn("boss_warning", arrival.events)

        armed = replace(arrival.state, enemies=(replace(boss, y=92, vy=0, shot_ms=0),))
        salvo = advance(armed, 0, rng=FixedRng())
        enemy_fire = [shot for shot in salvo.state.projectiles if shot.owner == "enemy"]
        self.assertEqual(len(enemy_fire), 5)

    def test_boss_defeat_awards_score_and_creates_large_explosion(self):
        boss = Enemy(1, "boss", 180, 92, 0, 0, 1, 1000, max_hp=50)
        state = replace(
            start(new_game()),
            level=5,
            kills=40,
            next_boss_level=10,
            enemies=(boss,),
            projectiles=(Projectile(180, 92, 0, 0, "player", damage=2),),
            fire_ms=1000,
        )
        transition = advance(state, 0, rng=FixedRng())
        self.assertEqual(transition.state.score, 3000)
        self.assertEqual(transition.state.explosions[0].kind, "boss")
        self.assertIn("boss_defeated", transition.events)

    def test_finished_explosions_are_removed(self):
        state = replace(
            start(new_game()),
            explosions=(Explosion(100, 100, "enemy", age_ms=450, duration_ms=460),),
            fire_ms=1000,
        )
        self.assertFalse(advance(state, 20, rng=FixedRng()).state.explosions)

    def test_shield_absorbs_a_projectile_without_losing_life(self):
        base = start(new_game())
        player = replace(base.player, shielded=True)
        state = replace(
            base,
            player=player,
            projectiles=(Projectile(player.x, player.y, 0, 0, "enemy"),),
            fire_ms=1000,
        )
        transition = advance(state, 0, rng=FixedRng())
        self.assertEqual(transition.state.player.lives, 3)
        self.assertFalse(transition.state.player.shielded)
        self.assertIn("shield", transition.events)

    def test_last_hit_ends_game_and_repair_cannot_revive_same_frame(self):
        base = start(new_game())
        player = replace(base.player, lives=1)
        state = replace(
            base,
            player=player,
            projectiles=(Projectile(player.x, player.y, 0, 0, "enemy"),),
            powerups=(PowerUp("repair", player.x, player.y, 0),),
            fire_ms=1000,
        )
        transition = advance(state, 0, rng=FixedRng())
        self.assertEqual(transition.state.status, "game_over")
        self.assertEqual(transition.state.player.lives, 0)
        self.assertIn("game_over", transition.events)

    def test_repair_pickup_restores_one_life(self):
        base = start(new_game())
        player = replace(base.player, lives=2)
        state = replace(
            base,
            player=player,
            powerups=(PowerUp("repair", player.x, player.y, 0),),
            fire_ms=1000,
        )
        transition = advance(state, 0, rng=FixedRng())
        self.assertEqual(transition.state.player.lives, 3)
        self.assertIn("powerup", transition.events)


if __name__ == "__main__":
    unittest.main()
