import pygame

# ---------- "classy" ----------

class Player:
    def __init__(self, x, y):
        self.w = 45
        self.h = 60
        self.x = x
        self.y = y
        self.vy = 0
        self.on_ground = False

    def jump(self):
        
        pass

    def update(self, dt, game):
        self.vy += game.gravity
        self.y += self.vy
        if self.y + self.h >= game.ground_y:
            self.y = game.ground_y - self.h
            self.vy = 0
            self.on_ground = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, screen):
        # pygame kresli obdelnik -> to je jako hrac
        pygame.draw.rect(screen, (0, 200, 255), self.rect())


class Obstacle:
    def __init__(self, x, y):
        self.w = 30
        self.h = 60
        self.x = x
        self.y = y

    def update(self, dt, game):
        # TODO: tady se to ma hejbat doleva, ale schvalne ne
        # kdybys chtel:
        # self.x -= game.scroll_speed
        pass

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, screen):
        # pygame kresli obdelnik -> to je jako prekazka
        pygame.draw.rect(screen, (255, 80, 80), self.rect())


class Game:
    def __init__(self):
        self.W = 900
        self.H = 450
        self.ground_y = 360

        self.gravity = 0.9
        self.scroll_speed = 7

        self.game_over = False

        self.player = Player(140, self.ground_y - 60)

        # jedna prekazka jen tak (zadnej spawn)
        self.obstacles = [
            Obstacle(650, self.ground_y - 60)
        ]

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    self.player.jump()

    def update(self, dt):
        if self.game_over:
            return

        self.player.update(dt, self)

        for ob in self.obstacles:
            ob.update(dt, self)

        # pygame rect kolize (tohle aspon funguje)
        for ob in self.obstacles:
            if self.player.rect().colliderect(ob.rect()):
                self.game_over = True

    def draw(self, screen):
        # pygame vyplni pozadi (aby to nebylo divny)
        screen.fill((25, 25, 30))

        # pygame nakresli zem (jen pruh)
        pygame.draw.rect(
            screen,
            (70, 70, 70),
            pygame.Rect(0, self.ground_y, self.W, self.H - self.ground_y)
        )

        self.player.draw(screen)
        for ob in self.obstacles:
            ob.draw(screen)

def main():
    # pygame start (jinak to nic neudela)
    pygame.init()

    # pygame okno
    screen = pygame.display.set_mode((900, 450))
    pygame.display.set_caption("Hop & Skok (jen kostra)")

    # pygame hodiny -> aby to nejelo 1000 fps
    clock = pygame.time.Clock()

    game = Game()

    run = True
    while run:
        # pygame dt (cas mezi framama)
        dt = clock.tick(60) / 1000.0

        # pygame eventy (klavesnice, zavreni okna...)
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                run = False

        game.handle_events(events)
        game.update(dt)
        game.draw(screen)

        # pygame prehodi obraz (jinak neuvidis nic)
        pygame.display.flip()

    # pygame konec
    pygame.quit()


# schvalne to je normalne spustitelny, ale "hra" neni hotova
# (nefunguje skok ani pohyb prekazek, takze je to jen kostra)
if __name__ == "__main__":
    main()
