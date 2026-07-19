import pygame
import webbrowser


MAKECODE_LINK = "https://makecode.com/_d0f8ii9ChCDk"


def run():

    pygame.init()

    WIDTH = 800
    HEIGHT = 450

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    pygame.display.set_caption("XboxOS Pong")

    clock = pygame.time.Clock()


    # Controller
    pygame.joystick.init()

    controller = None

    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()


    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)


    title_font = pygame.font.SysFont(None, 70)
    font = pygame.font.SysFont(None, 35)


    # ======================
    # MENU
    # ======================

    menu = True

    link_rect = pygame.Rect(
        200,
        330,
        400,
        50
    )


    while menu:

        screen.fill(BLACK)


        title = title_font.render(
            "XboxOS Pong",
            True,
            WHITE
        )

        screen.blit(
            title,
            (220, 70)
        )


        start = font.render(
            "A  Start Game",
            True,
            WHITE
        )

        exit_text = font.render(
            "B  Exit",
            True,
            WHITE
        )


        link = font.render(
            "Open MakeCode Arcade Version",
            True,
            WHITE
        )


        screen.blit(
            start,
            (280, 200)
        )

        screen.blit(
            exit_text,
            (280, 250)
        )


        pygame.draw.rect(
            screen,
            WHITE,
            link_rect,
            2
        )


        screen.blit(
            link,
            (220, 340)
        )


        pygame.display.flip()


        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                return


            # Controller buttons
            if event.type == pygame.JOYBUTTONDOWN:

                # A
                if event.button == 0:
                    menu = False

                # B
                elif event.button == 1:
                    pygame.quit()
                    return


            # Mouse click
            if event.type == pygame.MOUSEBUTTONDOWN:

                if link_rect.collidepoint(event.pos):

                    webbrowser.open(
                        MAKECODE_LINK
                    )


        clock.tick(60)



    # ======================
    # PONG GAME
    # ======================


    paddle_w = 15
    paddle_h = 100


    player = pygame.Rect(
        40,
        HEIGHT // 2 - paddle_h // 2,
        paddle_w,
        paddle_h
    )


    enemy = pygame.Rect(
        WIDTH - 55,
        HEIGHT // 2 - paddle_h // 2,
        paddle_w,
        paddle_h
    )


    ball = pygame.Rect(
        WIDTH // 2,
        HEIGHT // 2,
        15,
        15
    )


    ball_x = 6
    ball_y = 6


    player_score = 0
    enemy_score = 0


    score_font = pygame.font.SysFont(
        None,
        60
    )


    running = True


    while running:


        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False


            if event.type == pygame.JOYBUTTONDOWN:

                # B exit
                if event.button == 1:
                    running = False



        # Controller movement

        if controller:

            y = controller.get_axis(1)

            if abs(y) > 0.15:

                player.y += int(
                    y * 8
                )


        # Keyboard fallback

        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            player.y -= 8

        if keys[pygame.K_DOWN]:
            player.y += 8



        # Keep player inside

        player.y = max(
            0,
            min(
                HEIGHT - paddle_h,
                player.y
            )
        )


        # AI

        if enemy.centery < ball.centery:
            enemy.y += 5

        if enemy.centery > ball.centery:
            enemy.y -= 5



        # Ball movement

        ball.x += ball_x
        ball.y += ball_y


        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball_y *= -1



        if ball.colliderect(player):

            ball_x *= -1


        if ball.colliderect(enemy):

            ball_x *= -1



        # Score

        if ball.left <= 0:

            enemy_score += 1

            ball.center = (
                WIDTH // 2,
                HEIGHT // 2
            )

            ball_x = 6



        if ball.right >= WIDTH:

            player_score += 1

            ball.center = (
                WIDTH // 2,
                HEIGHT // 2
            )

            ball_x = -6



        # Draw

        screen.fill(BLACK)


        pygame.draw.rect(
            screen,
            WHITE,
            player
        )


        pygame.draw.rect(
            screen,
            WHITE,
            enemy
        )


        pygame.draw.ellipse(
            screen,
            WHITE,
            ball
        )


        score = score_font.render(
            f"{player_score}  {enemy_score}",
            True,
            WHITE
        )


        screen.blit(
            score,
            (350, 20)
        )


        pygame.display.flip()


        clock.tick(60)



    pygame.quit()