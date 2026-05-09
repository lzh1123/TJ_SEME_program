// 图标组件定义 - 使用h函数渲染
import { h } from 'vue'

// 创建SVG路径的辅助函数
const createPath = (d, attrs = {}) => h('path', { d, ...attrs })
const createCircle = (cx, cy, r, attrs = {}) => h('circle', { cx, cy, r, ...attrs })
const createRect = (x, y, width, height, attrs = {}) => h('rect', { x, y, width, height, ...attrs })
const createPolygon = (points, attrs = {}) => h('polygon', { points, ...attrs })

const defaultStroke = {
  stroke: 'currentColor',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round',
  fill: 'none'
}

export const search = {
  render() {
    return [
      createPath('M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z', defaultStroke)
    ]
  }
}

export const plus = {
  render() {
    return [createPath('M12 5V19M5 12H19', defaultStroke)]
  }
}

export const magic = {
  render() {
    return [createPath('M12 2L14.4 9.6L22 12L14.4 14.4L12 22L9.6 14.4L2 12L9.6 9.6L12 2Z', defaultStroke)]
  }
}

export const cloudUpload = {
  render() {
    return [
      createPath('M7 16C4.23858 16 2 13.7614 2 11C2 8.43442 3.90575 6.3276 6.36574 6.07266C6.88165 3.64505 9.05836 2 11.5 2C14.0778 2 16.2452 3.81002 16.6836 6.28299C19.0622 6.53208 21 8.72372 21 11.5C21 14.5376 18.5376 17 15.5 17', defaultStroke),
      createPath('M12 12V22M12 12L8 16M12 12L16 16', defaultStroke)
    ]
  }
}

export const paperclip = {
  render() {
    return [createPath('M21.44 11.05L12.25 20.24C10.56 21.93 8.04 21.93 6.35 20.24C4.66 18.55 4.66 16.03 6.35 14.34L15.54 5.15C16.63 4.06 18.37 4.06 19.46 5.15C20.55 6.24 20.55 7.98 19.46 9.07L10.27 18.26C9.72 18.81 8.84 18.81 8.29 18.26C7.74 17.71 7.74 16.83 8.29 16.28L16.72 7.85', defaultStroke)]
  }
}

export const trash = {
  render() {
    return [
      createPath('M3 6H5H21', defaultStroke),
      createPath('M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z', defaultStroke)
    ]
  }
}

export const times = {
  render() {
    return [createPath('M18 6L6 18M6 6L18 18', defaultStroke)]
  }
}

export const check = {
  render() {
    return [createPath('M20 6L9 17L4 12', defaultStroke)]
  }
}

export const arrowRight = {
  render() {
    return [createPath('M5 12H19M19 12L12 5M19 12L12 19', defaultStroke)]
  }
}

export const arrowLeft = {
  render() {
    return [createPath('M19 12H5M5 12L12 5M5 12L12 19', defaultStroke)]
  }
}

export const edit = {
  render() {
    return [
      createPath('M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13', defaultStroke),
      createPath('M18.5 2.5C18.8978 2.10218 19.4374 1.87868 20 1.87868C20.5626 1.87868 21.1022 2.10218 21.5 2.5C21.8978 2.89782 22.1213 3.43739 22.1213 4C22.1213 4.56261 21.8978 5.10218 21.5 5.5L12 15L8 16L9 12L18.5 2.5Z', defaultStroke)
    ]
  }
}

export const clock = {
  render() {
    return [
      createCircle('12', '12', '10', defaultStroke),
      createPath('M12 6V12L16 14', defaultStroke)
    ]
  }
}

export const save = {
  render() {
    return [
      createPath('M19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16L21 8V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21Z', defaultStroke),
      createPath('M17 21V13H7V21', defaultStroke),
      createPath('M7 3V8H15', defaultStroke)
    ]
  }
}

export const share = {
  render() {
    return [
      createCircle('18', '5', '3', defaultStroke),
      createCircle('6', '12', '3', defaultStroke),
      createCircle('18', '19', '3', defaultStroke),
      createPath('M8.59 13.51L15.42 17.49M15.41 6.51L8.59 10.49', defaultStroke)
    ]
  }
}

export const download = {
  render() {
    return [
      createPath('M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15', defaultStroke),
      createPath('M7 10L12 15L17 10', defaultStroke),
      createPath('M12 15V3', defaultStroke)
    ]
  }
}

export const chevronDown = {
  render() {
    return [createPath('M6 9L12 15L18 9', defaultStroke)]
  }
}

export const chevronRight = {
  render() {
    return [createPath('M9 18L15 12L9 6', defaultStroke)]
  }
}

export const list = {
  render() {
    return [
      createPath('M8 6H21M8 12H21M8 18H21', defaultStroke),
      createPath('M3 6H3.01M3 12H3.01M3 18H3.01', defaultStroke)
    ]
  }
}

export const images = {
  render() {
    return [
      createRect('3', '3', '18', '18', { ...defaultStroke, rx: '2', ry: '2' }),
      createCircle('8.5', '8.5', '1.5', defaultStroke),
      createPath('M21 15L16 10L5 21', defaultStroke)
    ]
  }
}

export const cog = {
  render() {
    return [
      createCircle('12', '12', '3', defaultStroke),
      createPath('M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5843 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6643 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4467 14.532 19.6572 14.3543 19.9255C14.1766 20.1937 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.258 9.77251 19.9887C9.5799 19.7194 9.31074 19.5143 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75524 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75524 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6643 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.742 9.96512 4.0113 9.77251C4.28059 9.5799 4.48572 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67524 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67524 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75524 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75524 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29577 4.55324 9.54802 4.34276 9.72569 4.07447C9.90337 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67524 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67524 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29577 19.6572 9.54802 19.9255 9.72569C20.1937 9.90337 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15V15Z', defaultStroke)
    ]
  }
}

export const robot = {
  render() {
    return [
      createRect('3', '11', '18', '10', { ...defaultStroke, rx: '2' }),
      createCircle('12', '5', '2', defaultStroke),
      createPath('M12 7V11', defaultStroke),
      createPath('M8 16H8.01M12 16H12.01M16 16H16.01', defaultStroke)
    ]
  }
}

export const paperPlane = {
  render() {
    return [createPath('M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13', defaultStroke)]
  }
}

export const undo = {
  render() {
    return [
      createPath('M3 7V13H9', defaultStroke),
      createPath('M21 17C21 14.2386 19.7614 11.7614 17.7614 9.76142C15.7614 7.76142 13.2843 6.52286 10.5229 6.52286L3 6.52286', defaultStroke)
    ]
  }
}

export const redo = {
  render() {
    return [
      createPath('M21 7V13H15', defaultStroke),
      createPath('M3 17C3 14.2386 4.23858 11.7614 6.23858 9.76142C8.23858 7.76142 10.7157 6.52286 13.4771 6.52286L21 6.52286', defaultStroke)
    ]
  }
}

export const thLarge = {
  render() {
    return [
      createRect('3', '3', '7', '7', { ...defaultStroke, rx: '1' }),
      createRect('14', '3', '7', '7', { ...defaultStroke, rx: '1' }),
      createRect('14', '14', '7', '7', { ...defaultStroke, rx: '1' }),
      createRect('3', '14', '7', '7', { ...defaultStroke, rx: '1' })
    ]
  }
}

export const palette = {
  render() {
    return [
      createCircle('12', '12', '10', defaultStroke),
      createPath('M12 2C10.9 2 10 2.9 10 4C10 5.1 10.9 6 12 6C13.1 6 14 5.1 14 4', defaultStroke),
      createPath('M12 22C13.1 22 14 21.1 14 20C14 18.9 13.1 18 12 18C10.9 18 10 18.9 10 20', defaultStroke),
      createPath('M22 12C22 10.9 21.1 10 20 10C18.9 10 18 10.9 18 12C18 13.1 18.9 14 20 14', defaultStroke),
      createPath('M2 12C2 13.1 2.9 14 4 14C5.1 14 6 13.1 6 12C6 10.9 5.1 10 4 10', defaultStroke)
    ]
  }
}

export const minus = {
  render() {
    return [createPath('M5 12H19', defaultStroke)]
  }
}

export const play = {
  render() {
    return [createPolygon('5 3 19 12 5 21 5 3', defaultStroke)]
  }
}

export const image = {
  render() {
    return [
      createRect('3', '3', '18', '18', { ...defaultStroke, rx: '2', ry: '2' }),
      createCircle('8.5', '8.5', '1.5', defaultStroke),
      createPath('M21 15L16 10L5 21', defaultStroke)
    ]
  }
}

export const chartBar = {
  render() {
    return [createPath('M18 20V10M12 20V4M6 20V14', defaultStroke)]
  }
}

export const infoCircle = {
  render() {
    return [
      createCircle('12', '12', '10', defaultStroke),
      createPath('M12 16V12M12 8H12.01', defaultStroke)
    ]
  }
}

export const checkCircle = {
  render() {
    return [
      createPath('M22 11.08V12C21.9988 14.1564 21.3005 16.2547 20.0093 17.9818C18.7182 19.709 16.9033 20.9725 14.8354 21.5839C12.7674 22.1953 10.5573 22.1219 8.53447 21.3746C6.51168 20.6273 4.78465 19.2461 3.61096 17.4371C2.43727 15.628 1.87979 13.4881 2.02168 11.3363C2.16356 9.18455 2.99721 7.13631 4.39828 5.49706C5.79935 3.85781 7.69279 2.71537 9.79619 2.24013C11.8996 1.7649 14.1003 1.98232 16.07 2.85999', defaultStroke),
      createPath('M22 4L12 14.01L9 11.01', defaultStroke)
    ]
  }
}

export const spinner = {
  render() {
    return [createPath('M12 2V6M12 18V22M6 12H2M22 12H18M19.07 4.93L16.24 7.76M7.76 16.24L4.93 19.07M19.07 19.07L16.24 16.24M7.76 7.76L4.93 4.93', defaultStroke)]
  }
}

export const sync = {
  render() {
    return [
      createPath('M21.5 2V8H15.5', defaultStroke),
      createPath('M2.5 22V16H8.5', defaultStroke),
      createPath('M2 11C2.93498 7.68038 5.23527 4.91132 8.3336 3.37624C11.4319 1.84116 15.0239 1.6713 18.251 2.90434', defaultStroke),
      createPath('M22 13C21.065 16.3196 18.7647 19.0887 15.6664 20.6238C12.5681 22.1588 8.97607 22.3287 5.74902 21.0957', defaultStroke)
    ]
  }
}

export const filePdf = {
  render() {
    return [
      createPath('M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z', defaultStroke),
      createPath('M14 2V8H20', defaultStroke),
      createPath('M10 13V17', defaultStroke),
      createPath('M14 13.5V16.5C14 17.0304 13.7893 17.5391 13.4142 17.9142C13.0391 18.2893 12.5304 18.5 12 18.5C11.4696 18.5 10.9609 18.2893 10.5858 17.9142C10.2107 17.5391 10 17.0304 10 16.5', defaultStroke)
    ]
  }
}

export const fileWord = {
  render() {
    return [
      createPath('M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z', defaultStroke),
      createPath('M14 2V8H20', defaultStroke),
      createPath('M9 13L11 17L13 13', defaultStroke),
      createPath('M16 13V17', defaultStroke)
    ]
  }
}

export const fileAlt = {
  render() {
    return [
      createPath('M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z', defaultStroke),
      createPath('M14 2V8H20', defaultStroke),
      createPath('M8 13H16', defaultStroke),
      createPath('M8 17H16', defaultStroke),
      createPath('M10 9H8', defaultStroke)
    ]
  }
}

export const fileCode = {
  render() {
    return [
      createPath('M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z', defaultStroke),
      createPath('M14 2V8H20', defaultStroke),
      createPath('M10 12L8 14L10 16', defaultStroke),
      createPath('M14 16L16 14L14 12', defaultStroke)
    ]
  }
}

export const filePowerpoint = {
  render() {
    return [
      createPath('M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z', defaultStroke),
      createPath('M14 2V8H20', defaultStroke),
      createPath('M9 13V17', defaultStroke),
      createPath('M9 13H12C12.5304 13 13.0391 13.2107 13.4142 13.5858C13.7893 13.9609 14 14.4696 14 15C14 15.5304 13.7893 16.0391 13.4142 16.4142C13.0391 16.7893 12.5304 17 12 17H9', defaultStroke)
    ]
  }
}

export const file = {
  render() {
    return [
      createPath('M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z', defaultStroke),
      createPath('M14 2V8H20', defaultStroke)
    ]
  }
}

export const help = {
  render() {
    return [
      createCircle('12', '12', '10', defaultStroke),
      createPath('M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.40913C11.0108 7.05016 11.7289 6.91894 12.4272 7.03871C13.1255 7.15849 13.7588 7.52154 14.2151 8.06353C14.6713 8.60553 14.9211 9.29152 14.92 10C14.92 12 11.92 13 11.92 13', defaultStroke),
      createCircle('12', '17', '0.5', defaultStroke)
    ]
  }
}

export const target = {
  render() {
    return [
      createCircle('12', '12', '10', defaultStroke),
      createCircle('12', '12', '6', defaultStroke),
      createCircle('12', '12', '2', defaultStroke)
    ]
  }
}
