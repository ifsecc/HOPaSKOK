import pygame
import settings


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def draw_text(screen, font, text, x, y, color=(240, 240, 240), center=True):
    img = font.render(text, True, color)
    rect = img.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(img, rect)
    return rect


def run_menu(screen, clock):
    title_font = pygame.font.SysFont("arial", 54, bold=True)
    font = pygame.font.SysFont("arial", 30, bold=True)
    small = pygame.font.SysFont("arial", 21, bold=True)

    selected = 0
    items = ["START", "NASTAVENÍ", "KONEC"]

    mode = "main"
    fov = settings.DEFAULT_FOV

    while True:
        clock.tick(settings.FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if mode == "settings":
                        mode = "main"
                    else:
                        return None

                if mode == "main":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(items)

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(items)

                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if items[selected] == "START":
                            return {"fov": fov}

                        elif items[selected] == "NASTAVENÍ":
                            mode = "settings"

                        elif items[selected] == "KONEC":
                            return None

                elif mode == "settings":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        fov = clamp(fov - 1, settings.FOV_MIN, settings.FOV_MAX)

                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        fov = clamp(fov + 1, settings.FOV_MIN, settings.FOV_MAX)

                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        mode = "main"

        screen.fill((12, 14, 22))

        pygame.draw.rect(
            screen,
            (18, 22, 36),
            (70, 70, settings.WIDTH - 140, settings.HEIGHT - 140),
            border_radius=24
        )

        pygame.draw.rect(
            screen,
            (80, 220, 255),
            (70, 70, settings.WIDTH - 140, settings.HEIGHT - 140),
            3,
            border_radius=24
        )

        draw_text(
            screen,
            title_font,
            "HOPASKOK",
            settings.WIDTH // 2,
            140,
            (255, 230, 120)
        )

        if mode == "main":
            draw_text(
                screen,
                small,
                "Šipky/W/S = pohyb   ENTER/SPACE = potvrdit",
                settings.WIDTH // 2,
                205,
                (190, 200, 220)
            )

            for i, item in enumerate(items):
                if i == selected:
                    color = (255, 160, 230)
                    prefix = "▶ "
                else:
                    color = (235, 240, 250)
                    prefix = "  "

                draw_text(
                    screen,
                    font,
                    prefix + item,
                    settings.WIDTH // 2,
                    290 + i * 58,
                    color
                )

        elif mode == "settings":
            draw_text(
                screen,
                font,
                "NASTAVENÍ",
                settings.WIDTH // 2,
                230,
                (255, 160, 230)
            )

            draw_text(
                screen,
                font,
                f"FOV: {fov}",
                settings.WIDTH // 2,
                325,
                (240, 240, 250)
            )

            draw_text(
                screen,
                small,
                "←/A snížit   →/D zvýšit   ENTER/SPACE zpět",
                settings.WIDTH // 2,
                385,
                (190, 200, 220)
            )

            slider_x = 260
            slider_y = 455
            slider_w = 380

            pygame.draw.rect(
                screen,
                (55, 65, 95),
                (slider_x, slider_y, slider_w, 10),
                border_radius=6
            )

            ratio = (fov - settings.FOV_MIN) / (settings.FOV_MAX - settings.FOV_MIN)
            knob_x = int(slider_x + ratio * slider_w)

            pygame.draw.circle(
                screen,
                (80, 220, 255),
                (knob_x, slider_y + 5),
                15
            )

        pygame.display.flip()
