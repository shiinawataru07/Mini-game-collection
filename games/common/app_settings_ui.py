"""Menu-hosted controls for collection-wide audio and display settings."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from .app_settings import AppSettings, audio_status
from .controls import draw_button, draw_overlay, draw_panel
from .fonts import get_font


@dataclass(frozen=True)
class AppSettingsControls:
    modal: pygame.Rect
    close: pygame.Rect
    volume_down: pygame.Rect
    volume_up: pygame.Rect
    mute: pygame.Rect
    fullscreen: pygame.Rect


def app_settings_controls(window_size: tuple[int, int]) -> AppSettingsControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(460, width - 36), min(360, height - 36))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 88, modal.top + 18, 66, 34)
    volume_down = pygame.Rect(modal.left + 40, modal.top + 116, 64, 44)
    volume_up = pygame.Rect(modal.right - 104, modal.top + 116, 64, 44)
    mute = pygame.Rect(modal.left + 40, modal.top + 205, modal.width - 80, 44)
    fullscreen = pygame.Rect(modal.left + 40, modal.top + 270, modal.width - 80, 44)
    return AppSettingsControls(modal, close, volume_down, volume_up, mute, fullscreen)


def draw_app_settings(screen: pygame.Surface, settings: AppSettings) -> AppSettingsControls:
    controls = app_settings_controls(screen.get_size())
    draw_overlay(screen, (28, 35, 31), 155)
    draw_panel(
        screen,
        controls.modal,
        (255, 255, 252),
        border_color=(201, 211, 202),
        border_width=2,
        border_radius=18,
    )
    title = get_font(28, "zh", bold=True).render("全局设置", True, (50, 61, 53))
    screen.blit(title, (controls.modal.left + 28, controls.modal.top + 22))
    draw_button(
        screen,
        controls.close,
        "关闭",
        (242, 244, 239),
        (50, 61, 53),
        15,
        "zh",
        border_color=(215, 222, 213),
    )
    volume_label = get_font(16, "zh").render("主音量", True, (106, 119, 108))
    screen.blit(
        volume_label, volume_label.get_rect(center=(controls.modal.centerx, modal_y(controls, 92)))
    )
    draw_button(screen, controls.volume_down, "−", (242, 244, 239), (50, 61, 53), 24)
    draw_button(screen, controls.volume_up, "+", (242, 244, 239), (50, 61, 53), 24)
    value = get_font(25, bold=True).render(f"{settings.volume}%", True, (50, 61, 53))
    screen.blit(
        value, value.get_rect(center=(controls.modal.centerx, controls.volume_down.centery))
    )
    mute_label = "取消静音" if settings.muted else "静音"
    draw_button(
        screen,
        controls.mute,
        f"{mute_label}  ·  M",
        (139, 116, 255) if settings.muted else (242, 244, 239),
        (255, 255, 255) if settings.muted else (50, 61, 53),
        17,
        "zh",
        border_color=(139, 116, 255),
    )
    fullscreen_label = "退出全屏" if settings.fullscreen else "进入全屏"
    draw_button(
        screen,
        controls.fullscreen,
        f"{fullscreen_label}  ·  F11",
        (242, 244, 239),
        (50, 61, 53),
        17,
        "zh",
        border_color=(215, 222, 213),
    )
    status = get_font(13, "zh").render(
        f"{audio_status(settings)}  ·  使用 - / + 调节",
        True,
        (106, 119, 108),
    )
    screen.blit(
        status, status.get_rect(center=(controls.modal.centerx, controls.modal.bottom - 19))
    )
    return controls


def modal_y(controls: AppSettingsControls, offset: int) -> int:
    return controls.modal.top + offset
