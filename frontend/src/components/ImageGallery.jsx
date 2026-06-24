import { Swiper, SwiperSlide } from 'swiper/react'
import { Pagination } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'

export default function ImageGallery({ images = [] }) {
  if (!images.length) {
    return (
      <div className="aspect-square bg-tg-card flex items-center justify-center text-5xl text-tg-muted">📷</div>
    )
  }

  return (
    <Swiper modules={[Pagination]} pagination={{ clickable: true }} className="aspect-square">
      {images.map((url, i) => (
        <SwiperSlide key={i}>
          <img src={url} alt="" className="w-full h-full object-cover" loading={i === 0 ? 'eager' : 'lazy'} />
        </SwiperSlide>
      ))}
    </Swiper>
  )
}
